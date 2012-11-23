# -*- coding: utf-8 -*-
import json
from mock import Mock

from nailgun.settings import settings
settings.update({
    'FAKE_TASKS': True,
    'FAKE_TASKS_TICK_INTERVAL': 1,
    'FAKE_TASKS_TICK_COUNT': 1,
})

import nailgun
from nailgun.test.base import BaseHandlers
from nailgun.test.base import reverse
from nailgun.api.models import Cluster, Attributes, IPAddr, Task


class TestTaskManagers(BaseHandlers):

    def test_deployment_task_managers(self):
        cluster = self.create_cluster_api()
        node1 = self.create_default_node(cluster_id=cluster['id'],
                                         pending_addition=True)
        node2 = self.create_default_node(cluster_id=cluster['id'],
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
        supertask = self.db.query(Task).filter_by(uuid=supertask_uuid).first()
        self.assertEquals(supertask.name, 'deploy')
        self.assertEquals(supertask.status, 'running')
        self.assertEquals(len(supertask.subtasks), 2)

    def test_network_verify_task_managers(self):
        cluster = self.create_cluster_api()
        node1 = self.create_default_node(cluster_id=cluster['id'])
        node2 = self.create_default_node(cluster_id=cluster['id'])
        resp = self.app.put(
            reverse(
                'ClusterNetworksHandler',
                kwargs={'cluster_id': cluster['id']}),
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
        response = json.loads(resp.body)
        task_uuid = response['uuid']
        task = self.db.query(Task).filter_by(uuid=task_uuid).first()
        self.assertEquals(task.name, 'verify_networks')
        self.assertEquals(task.status, 'running')
