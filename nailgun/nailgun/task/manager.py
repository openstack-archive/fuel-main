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
from nailgun.task.errors import DeploymentAlreadyStarted
from nailgun.task.errors import WrongNodeStatus
from nailgun.task.errors import DeletionAlreadyStarted

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
        if nodes_to_delete:
            supertask.create_subtask("node_deletion")
        if nodes_to_deploy:
            supertask.create_subtask("deployment")
        for subtask in supertask.subtasks:
            subtask.execute({
                'node_deletion': tasks.DeletionTask,
                'deployment': tasks.DeploymentTask,
            }[subtask.name])
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
                "Deleting cluster while deployment is still running"
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
