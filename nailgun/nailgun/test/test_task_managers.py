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
from nailgun.api.models import Cluster, Attributes, Task, Notification


class TestTaskManagers(BaseHandlers):

    def tearDown(self):
        # wait for fake task thread termination
        import threading
        for thread in threading.enumerate():
            if thread is not threading.currentThread():
                thread.join(1)

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
        self.assertIn(supertask.status, ('running', 'ready'))
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
        self.assertIn(task.status, ('running', 'ready'))

    def test_deletion_cluster_task_manager(self):
        cluster = self.create_cluster_api()
        resp = self.app.delete(
            reverse(
                'ClusterHandler',
                kwargs={'cluster_id': cluster['id']}),
            headers=self.default_headers
        )
        self.assertEquals(202, resp.status)

        # As far as DELETE method in ClusterHandler launches
        # asynchronous task which deletes cluster and all
        # related items including tasks, so we cannot be
        # sure that the cluster deletion task itself is still alive
        # However we can check "cluster deletion is done" notification
        task = self.db.query(Task)\
            .filter(Task.name == "cluster_deletion")\
            .filter(Task.cluster_id == cluster["id"])\
            .first()
        if task:
            self.assertIn(task.status, ('running', 'ready'))
        else:
            notification = self.db.query(Notification)\
                .filter(Notification.topic == "done")\
                .filter(Notification.message == "Cluster %s and all cluster "
                        "nodes are deleted" % cluster["name"])
            self.assertIsNotNone(notification)
