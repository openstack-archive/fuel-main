# -*- coding: utf-8 -*-

import uuid
import logging
import itertools

import web

from nailgun.settings import settings
from nailgun.api.models import Cluster
from nailgun.api.models import Task
from nailgun.api.models import Network
from nailgun.task.errors import DeploymentAlreadyStarted, WrongNodeStatus

from nailgun.task import task as original_tasks
from nailgun.task import fake as fake_tasks
tasks = settings.FAKE_TASKS and fake_tasks or original_tasks

logger = logging.getLogger(__name__)


class TaskManager(object):

    def __init__(self, cluster_id):
        self.cluster = web.ctx.orm.query(Cluster).get(cluster_id)


class DeploymentTaskManager(TaskManager):

    def execute(self):
        current_tasks = web.ctx.orm.query(Task).filter(
            Task.cluster == self.cluster,
            Task.name == "deploy"
        )
        for task in current_tasks:
            if task.status == "running":
                raise DeploymentAlreadyStarted()
            elif task.status in ("ready", "error"):
                for subtask in task.subtasks:
                    web.ctx.orm.delete(subtask)
                web.ctx.orm.delete(task)
                web.ctx.orm.commit()
        nodes_to_delete = filter(lambda n: n.pending_deletion,
                                 self.cluster.nodes)
        nodes_to_deploy = filter(lambda n: n.pending_addition,
                                 self.cluster.nodes)
        if not nodes_to_deploy and not nodes_to_delete:
            raise WrongNodeStatus("No changes to deploy")

        self.cluster.status = 'deployment'
        web.ctx.orm.add(self.cluster)
        web.ctx.orm.commit()

        supertask = Task(
            name="deploy",
            cluster=self.cluster
        )
        web.ctx.orm.add(supertask)
        web.ctx.orm.commit()
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
        web.ctx.orm.add(task)
        web.ctx.orm.commit()
        task.execute(tasks.VerifyNetworksTask)
        return task


class ClusterDeletionManager(TaskManager):

    def execute(self):
        current_cluster_tasks = web.ctx.orm.query(Task).filter(
            Task.cluster == self.cluster
        )

        logger.debug("Removing cluster tasks")
        for task in current_cluster_tasks:
            for subtask in task.subtasks:
                web.ctx.orm.delete(subtask)
            web.ctx.orm.delete(task)
            web.ctx.orm.commit()

        logger.debug("Labeling cluster nodes to delete")
        for node in self.cluster.nodes:
            node.pending_deletion = True
            web.ctx.orm.add(node)
            web.ctx.orm.commit()

        self.cluster.status = 'remove'
        web.ctx.orm.add(self.cluster)
        web.ctx.orm.commit()

        logger.debug("Creating nodes deletion task")
        task = Task(name="cluster_deletion", cluster=self.cluster)
        web.ctx.orm.add(task)
        web.ctx.orm.commit()
        task.execute(tasks.ClusterDeletionTask)
        return task
