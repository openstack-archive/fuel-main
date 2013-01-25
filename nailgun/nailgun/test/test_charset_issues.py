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
from nailgun.test.base import BaseHandlers
from nailgun.test.base import reverse
from nailgun.api.models import Cluster, Attributes, Task, Notification, Node


class TestCharsetIssues(BaseHandlers):

    @patch('nailgun.task.task.rpc.cast', nailgun.task.task.fake_cast)
    @patch('nailgun.task.task.settings.FAKE_TASKS', True)
    @patch('nailgun.task.fake.settings.FAKE_TASKS_TICK_COUNT', 80)
    @patch('nailgun.task.fake.settings.FAKE_TASKS_TICK_INTERVAL', 1)
    def test_deployment_cyrillic_names(self):
        cluster = self.create_cluster_api(name=u"Тестовый кластер")
        node1 = self.create_default_node(cluster_id=cluster['id'],
                                         role="controller",
                                         name=u"Контроллер",
                                         status="discover",
                                         pending_addition=True)
        node2 = self.create_default_node(cluster_id=cluster['id'],
                                         status="ready",
                                         role="compute",
                                         name=u"Компьют",
                                         pending_addition=True)
        node3 = self.create_default_node(cluster_id=cluster['id'],
                                         pending_deletion=True)
        resp = self.app.put(
            reverse(
                'ClusterChangesHandler',
                kwargs={'cluster_id': cluster['id']}),
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
        response = json.loads(resp.body)
        supertask_uuid = response['uuid']
        supertask = self.db.query(Task).filter_by(
            uuid=supertask_uuid
        ).first()
        self.assertEquals(supertask.name, 'deploy')
        self.assertIn(supertask.status, ('running', 'ready'))
        self.assertEquals(len(supertask.subtasks), 2)

        timer = time.time()
        timeout = 10
        while True:
            self.db.refresh(node1)
            self.db.refresh(node2)
            if node1.status in ('provisioning', 'provisioned') and \
                    node2.status == 'provisioned':
                break
            if time.time() - timer > timeout:
                raise Exception("Something wrong with the statuses")
            time.sleep(1)

        timer = time.time()
        timeout = 60
        while supertask.status == 'running':
            self.db.refresh(supertask)
            if time.time() - timer > timeout:
                raise Exception("Deployment seems to be hanged")
            time.sleep(1)

        self.assertEquals(supertask.status, 'ready')
        self.assertEquals(supertask.progress, 100)
