# -*- coding: utf-8 -*-

import json
import time

from mock import patch

from nailgun.settings import settings

import nailgun
import nailgun.rpc as rpc
from nailgun.task.manager import DeploymentTaskManager
from nailgun.task.fake import FAKE_THREADS
from nailgun.test.base import Environment
from nailgun.test.base import BaseHandlers
from nailgun.test.base import reverse
from nailgun.test.base import fake_tasks
from nailgun.api.models import Cluster, Attributes, Task, Notification, Node


class TestCharsetIssues(BaseHandlers):

    def tearDown(self):
        super(TestCharsetIssues, self).tearDown()
        self._wait_for_threads()

    @fake_tasks()
    def test_deployment_cyrillic_names(self):
        self.env.create(
            cluster_kwargs={"name": u"Тестовый кластер"},
            nodes_kwargs=[
                {"name": u"Контроллер", "pending_addition": True},
                {"name": u"Компьют", "pending_addition": True},
                {"pending_deletion": True},
            ]
        )
        supertask = self.env.launch_deployment()
        self.assertEquals(supertask.name, 'deploy')
        self.assertIn(supertask.status, ('running', 'ready'))
        self.assertEquals(len(supertask.subtasks), 2)

        self.env.wait_for_nodes_status(self.env.nodes, 'provisioning')
        self.env.wait_ready(supertask, 60)

    @fake_tasks()
    def test_deletion_during_deployment(self):
        self.env.create(
            cluster_kwargs={
                "name": u"Вася"
            },
            nodes_kwargs=[
                {"status": "ready",  "pending_addition": True},
            ]
        )
        cluster_id = self.env.clusters[0].id
        resp = self.app.put(
            reverse(
                'ClusterChangesHandler',
                kwargs={'cluster_id': cluster_id}),
            headers=self.default_headers
        )
        resp = self.app.delete(
            reverse(
                'ClusterHandler',
                kwargs={'cluster_id': cluster_id}),
            headers=self.default_headers
        )
        timeout = 10
        timer = time.time()
        while True:
            task_delete = self.db.query(Task).filter_by(
                cluster_id=cluster_id,
                name="cluster_deletion"
            ).first()
            if not task_delete:
                break
            self.db.expire(task_delete)
            if (time.time() - timer) > timeout:
                raise Exception("Cluster deletion timeout")
            time.sleep(0.24)

        cluster_db = self.db.query(Cluster).get(cluster_id)
        self.assertIsNone(cluster_db)
