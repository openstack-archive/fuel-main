# -*- coding: utf-8 -*-

import uuid
import logging
import itertools

import web

from nailgun.db import orm
from nailgun.settings import settings
from nailgun.api.models import Cluster
from nailgun.api.models import Task
from nailgun.api.models import Network
from nailgun.task.helpers import update_task_status
from nailgun.task.errors import DeploymentAlreadyStarted
from nailgun.task.errors import WrongNodeStatus
from nailgun.task.errors import DeletionAlreadyStarted
from nailgun.task.errors import AssignIPError
from nailgun.task.errors import FailedProvisioning

from nailgun.task import task as tasks

logger = logging.getLogger(__name__)


class TaskManager(object):

    def __init__(self, cluster_id):
        self.cluster = orm().query(Cluster).get(cluster_id)


class DeploymentTaskManager(TaskManager):

    def execute(self):
        current_tasks = orm().query(Task).filter(
            Task.cluster == self.cluster,
            Task.name == "deploy"
        )
        for task in current_tasks:
            if task.status == "running":
                raise DeploymentAlreadyStarted()
            elif task.status in ("ready", "error"):
                for subtask in task.subtasks:
                    orm().delete(subtask)
                orm().delete(task)
                orm().commit()
        nodes_to_delete = filter(lambda n: n.pending_deletion,
                                 self.cluster.nodes)
        nodes_to_deploy = filter(lambda n: n.pending_addition,
                                 self.cluster.nodes)
        if not nodes_to_deploy and not nodes_to_delete:
            raise WrongNodeStatus("No changes to deploy")

        self.cluster.status = 'deployment'
        orm().add(self.cluster)
        orm().commit()

        supertask = Task(
            name="deploy",
            cluster=self.cluster
        )
        orm().add(supertask)
        orm().commit()
        task_deletion, task_deployment = None, None
        if nodes_to_delete:
            task_deletion = supertask.create_subtask("node_deletion")
        if nodes_to_deploy:
            task_deployment = supertask.create_subtask("deployment")

        if task_deletion:
            task_deletion.execute(tasks.DeletionTask)
        if task_deployment:
            err = None
            try:
                task_deployment.execute(tasks.DeploymentTask)
            except AssignIPError:
                err = "Failed to assign IP no node(s)"
            except FailedProvisioning:
                err = "Failed to provision node(s)"
            except Exception as ex:
                err = str(ex)
            if err:
                update_task_status(
                    task_deployment.uuid,
                    status="error",
                    progress=100,
                    msg=err
                )
                orm().commit()

        return supertask


class VerifyNetworksTaskManager(TaskManager):

    def execute(self):
        task = Task(
            name="verify_networks",
            cluster=self.cluster
        )
        orm().add(task)
        orm().commit()
        task.execute(tasks.VerifyNetworksTask)
        return task


class ClusterDeletionManager(TaskManager):

    def execute(self):
        current_cluster_tasks = orm().query(Task).filter(
            Task.cluster == self.cluster,
            Task.name == 'cluster_deletion'
        )
        deploy_running = orm().query(Task).filter(
            Task.cluster == self.cluster,
            Task.name == 'deploy',
            Task.status == 'running'
        )
        if deploy_running:
            logger.error(
                "Deleting cluster '{0}' "
                "while deployment is still running".format(
                    self.cluster.name
                )
            )

        logger.debug("Removing cluster tasks")
        for task in current_cluster_tasks:
            if task.status == "running":
                raise DeletionAlreadyStarted()
            elif task.status in ("ready", "error"):
                for subtask in task.subtasks:
                    orm().delete(subtask)
                orm().delete(task)
                orm().commit()

        logger.debug("Labeling cluster nodes to delete")
        for node in self.cluster.nodes:
            node.pending_deletion = True
            orm().add(node)
            orm().commit()

        self.cluster.status = 'remove'
        orm().add(self.cluster)
        orm().commit()

        logger.debug("Creating nodes deletion task")
        task = Task(name="cluster_deletion", cluster=self.cluster)
        orm().add(task)
        orm().commit()
        task.execute(tasks.ClusterDeletionTask)
        return task
