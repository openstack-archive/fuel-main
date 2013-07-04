# -*- coding: utf-8 -*-

#    Copyright 2013 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import uuid
import logging
import itertools
import traceback

import web

from nailgun.db import db
import nailgun.rpc as rpc
from nailgun.logger import logger
from nailgun.errors import errors
from nailgun.api.models import Cluster
from nailgun.api.models import Task
from nailgun.api.models import Network
from nailgun.task.task import TaskHelper

from nailgun.task import task as tasks


class TaskManager(object):

    def __init__(self, cluster_id=None):
        if cluster_id:
            self.cluster = db().query(Cluster).get(cluster_id)

    def _call_silently(self, task, instance, *args, **kwargs):
        method = getattr(instance, kwargs.pop('method_name', 'execute'))
        if task.status == 'error':
            return
        try:
            return method(task, *args, **kwargs)
        except Exception as exc:
            err = str(exc)
            if any([
                not hasattr(exc, "log_traceback"),
                hasattr(exc, "log_traceback") and exc.log_traceback
            ]):
                logger.error(traceback.format_exc())
            TaskHelper.update_task_status(
                task.uuid,
                status="error",
                progress=100,
                msg=err
            )


class DeploymentTaskManager(TaskManager):

    def execute(self):
        logger.info(
            u"Trying to start deployment at cluster '{0}'".format(
                self.cluster.name or self.cluster.id,
            )
        )
        current_tasks = db().query(Task).filter_by(
            cluster_id=self.cluster.id,
            name="deploy"
        )
        for task in current_tasks:
            if task.status == "running":
                raise errors.DeploymentAlreadyStarted()
            elif task.status in ("ready", "error"):
                for subtask in task.subtasks:
                    db().delete(subtask)
                db().delete(task)
                db().commit()

        nodes_to_delete = TaskHelper.nodes_to_delete(self.cluster)
        nodes_to_deploy = TaskHelper.nodes_to_deploy(self.cluster)
        nodes_to_provision = TaskHelper.nodes_to_provision(self.cluster)

        if not any([nodes_to_provision, nodes_to_deploy, nodes_to_delete]):
            raise errors.WrongNodeStatus("No changes to deploy")

        self.cluster.status = 'deployment'
        db().add(self.cluster)
        db().commit()

        supertask = Task(
            name="deploy",
            cluster=self.cluster
        )
        db().add(supertask)
        db().commit()
        task_deletion, task_provision, task_deployment = None, None, None

        if nodes_to_delete:
            task_deletion = supertask.create_subtask("node_deletion")
            logger.debug("Launching deletion task: %s", task_deletion.uuid)
            self._call_silently(
                task_deletion,
                tasks.DeletionTask
            )

        task_messages = []
        if nodes_to_provision:
            TaskHelper.update_slave_nodes_fqdn(nodes_to_provision)
            logger.debug("There are nodes to provision: %s",
                         " ".join([n.fqdn for n in nodes_to_provision]))
            task_provision = supertask.create_subtask("provision")
            # we assume here that task_provision just adds system to
            # cobbler and reboots it, so it has extremely small weight
            task_provision.weight = 0.05
            provision_message = self._call_silently(
                task_provision,
                tasks.ProvisionTask,
                method_name='message'
            )
            task_provision.cache = provision_message
            db().add(task_provision)
            db().commit()
            task_messages.append(provision_message)

        if nodes_to_deploy:
            TaskHelper.update_slave_nodes_fqdn(nodes_to_deploy)
            logger.debug("There are nodes to deploy: %s",
                         " ".join([n.fqdn for n in nodes_to_deploy]))
            task_deployment = supertask.create_subtask("deployment")
            deployment_message = self._call_silently(
                task_deployment,
                tasks.DeploymentTask,
                method_name='message'
            )
            task_deployment.cache = deployment_message
            db().add(task_deployment)
            db().commit()
            task_messages.append(deployment_message)

        if task_messages:
            rpc.cast('naily', task_messages)

        logger.debug(
            u"Deployment: task to deploy cluster '{0}' is {1}".format(
                self.cluster.name or self.cluster.id,
                supertask.uuid
            )
        )
        return supertask


class CheckBeforeDeploymentTaskManager(TaskManager):

    def execute(self):
        task = Task(
            name='check_before_deployment',
            cluster=self.cluster
        )
        db().add(task)
        db().commit()
        self._call_silently(task, tasks.CheckBeforeDeploymentTask)
        db().refresh(task)
        if task.status == 'running':
            TaskHelper.update_task_status(
                task.uuid, status="ready", progress=100)

        return task


class CheckNetworksTaskManager(TaskManager):

    def execute(self, data):
        task = Task(
            name="check_networks",
            cluster=self.cluster
        )
        db().add(task)
        db().commit()
        self._call_silently(
            task,
            tasks.CheckNetworksTask,
            data
        )
        db().refresh(task)
        if task.status == 'running':
            TaskHelper.update_task_status(
                task.uuid,
                status="ready",
                progress=100
            )
        return task


class VerifyNetworksTaskManager(TaskManager):

    def execute(self, nets, vlan_ids):
        task = Task(
            name="check_networks",
            cluster=self.cluster
        )
        db().add(task)
        db().commit()
        self._call_silently(
            task,
            tasks.CheckNetworksTask,
            nets
        )
        db().refresh(task)
        if task.status != 'error':
            # this one is connected with UI issues - we need to
            # separate if error happened inside nailgun or somewhere
            # in the orchestrator, and UI does it by task name.
            task.name = "verify_networks"
            db().add(task)
            db().commit()
            self._call_silently(
                task,
                tasks.VerifyNetworksTask,
                vlan_ids
            )
        return task


class ClusterDeletionManager(TaskManager):

    def execute(self):
        current_cluster_tasks = db().query(Task).filter_by(
            cluster=self.cluster,
            name='cluster_deletion'
        ).all()
        deploy_running = db().query(Task).filter_by(
            cluster=self.cluster,
            name='deploy',
            status='running'
        ).first()
        if deploy_running:
            logger.error(
                u"Deleting cluster '{0}' "
                "while deployment is still running".format(
                    self.cluster.name
                )
            )

        logger.debug("Removing cluster tasks")
        for task in current_cluster_tasks:
            if task.status == "running":
                raise errors.DeletionAlreadyStarted()
            elif task.status in ("ready", "error"):
                for subtask in task.subtasks:
                    db().delete(subtask)
                db().delete(task)
                db().commit()

        logger.debug("Labeling cluster nodes to delete")
        for node in self.cluster.nodes:
            node.pending_deletion = True
            db().add(node)
            db().commit()

        self.cluster.status = 'remove'
        db().add(self.cluster)
        db().commit()

        logger.debug("Creating cluster deletion task")
        task = Task(name="cluster_deletion", cluster=self.cluster)
        db().add(task)
        db().commit()
        self._call_silently(
            task,
            tasks.ClusterDeletionTask
        )
        return task


class DownloadReleaseTaskManager(TaskManager):

    def __init__(self, release_data):
        self.release_data = release_data

    def execute(self):
        logger.debug("Creating release dowload task")
        task = Task(name="download_release")
        db().add(task)
        db().commit()
        self._call_silently(
            task,
            tasks.DownloadReleaseTask,
            self.release_data
        )
        return task
