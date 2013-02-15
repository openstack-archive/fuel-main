# -*- coding: utf-8 -*-

import json
import time

from mock import patch

from nailgun.settings import settings

import nailgun
import nailgun.rpc as rpc
from nailgun.task.manager import DeploymentTaskManager
from nailgun.task.fake import FAKE_THREADS
from nailgun.task.errors import WrongNodeStatus
from nailgun.test.base import Environment
from nailgun.test.base import BaseHandlers
from nailgun.test.base import reverse
from nailgun.test.base import fake_tasks
from nailgun.api.models import Cluster, Attributes, Task, Notification, Node


class TestCharsetIssues(BaseHandlers):

    def tearDown(self):
        self._wait_for_threads()

    @fake_tasks()
    def test_deployment_cyrillic_names(self):
        self.env.create(
            cluster_kwargs={"name": u"Тестовый кластер"},
            nodes_kwargs=[
                {"name": u"Контроллер", "pending_addition": True},
                {"name": u"Компьют", "status": "ready",
                 "pending_addition": True},
                {"pending_deletion": True},
            ]
        )
        supertask = self.env.launch_deployment()
        self.assertEquals(supertask.name, 'deploy')
        self.assertIn(supertask.status, ('running', 'ready'))
        self.assertEquals(len(supertask.subtasks), 2)

        timer = time.time()
        timeout = 10
        while True:
            self.env.refresh_nodes()
            if self.env.nodes[0].status in \
                    ('provisioning', 'provisioned') and \
                    self.env.nodes[1].status == 'provisioned':
                break
            if time.time() - timer > timeout:
                raise Exception("Something wrong with the statuses")
            time.sleep(1)

        self.env.wait_ready(supertask, 60)
