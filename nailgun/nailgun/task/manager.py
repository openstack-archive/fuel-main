# -*- coding: utf-8 -*-

import uuid
import logging
import itertools

import web

from nailgun.settings import settings
from nailgun.api.models import Cluster
from nailgun.api.models import Task
from nailgun.task.task import DeploymentTask
from nailgun.task.task import DeletionTask
from nailgun.task.task import VerifyNetworksTask

logger = logging.getLogger(__name__)


class TaskManager(object):

    def __init__(self, cluster_id):
        self.cluster = web.ctx.orm.query(Cluster).get(cluster_id)


class DeploymentTaskManager(TaskManager):

    def execute(self):
        q = web.ctx.orm.query(Task).filter(
            Task.cluster == self.cluster,
            Task.name == "deploy"
        )
        for t in q:
            if t.status == "running":
                raise DeploymentAlreadyStarted()
            elif t.status in ("ready", "error"):
                web.ctx.orm.delete(t)
                web.ctx.orm.commit()
        self.super_task = Task(
            name="deploy",
            cluster=self.cluster
        )
        web.ctx.orm.add(self.super_task)
        web.ctx.orm.commit()
        self.deletion_task = self.super_task.create_subtask("deletion")
        self.deployment_task = self.super_task.create_subtask("deployment")
        self.deletion_task.execute(DeletionTask)
        self.deployment_task.execute(DeploymentTask)
        # note: this will work only in sync mode
        self.super_task.refresh()
        return self.super_task


class VerifyNetworksTaskManager(TaskManager):

    def execute(self):
        self.task = Task(
            name="verify_networks",
            cluster=self.cluster
        )
        web.ctx.orm.add(self.task)
        web.ctx.orm.commit()
        self.task.execute(VerifyNetworksTask)
        return self.task
