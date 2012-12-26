# -*- coding: utf-8 -*-
import json
import time

from mock import Mock, patch

from nailgun.settings import settings

import nailgun
import nailgun.rpc as rpc
from nailgun.task.fake import FAKE_THREADS
from nailgun.test.base import BaseHandlers
from nailgun.test.base import reverse
from nailgun.api.models import Cluster, Attributes, Task, Notification, Node


class TestTaskManagers(BaseHandlers):

    def setUp(self):
        super(TestTaskManagers, self).setUp()

    def tearDown(self):
        # wait for fake task thread termination
        import threading
        for thread in threading.enumerate():
            if thread is not threading.currentThread():
                thread.join(
                    int(settings.FAKE_TASKS_TICK_COUNT) *
                    int(settings.FAKE_TASKS_TICK_INTERVAL) + 5
                )

    @patch('nailgun.task.task.rpc.cast', nailgun.task.task.fake_cast)
    @patch('nailgun.task.task.settings.FAKE_TASKS', True)
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
        supertask = self.db.query(Task).filter_by(
            uuid=supertask_uuid
        ).first()
        self.assertEquals(supertask.name, 'deploy')
        self.assertIn(supertask.status, ('running', 'ready'))
        self.assertEquals(len(supertask.subtasks), 2)

    @patch('nailgun.task.task.rpc.cast', nailgun.task.task.fake_cast)
    @patch('nailgun.task.task.settings.FAKE_TASKS', True)
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

    @patch('nailgun.task.task.rpc.cast', nailgun.task.task.fake_cast)
    @patch('nailgun.task.task.settings.FAKE_TASKS', True)
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

    @patch('nailgun.task.task.rpc.cast', nailgun.task.task.fake_cast)
    @patch('nailgun.task.task.settings.FAKE_TASKS', True)
    def test_deletion_during_deployment(self):
        cluster = self.create_cluster_api()
        node1 = self.create_default_node(cluster_id=cluster['id'],
                                         pending_addition=True)
        resp = self.app.put(
            reverse(
                'ClusterChangesHandler',
                kwargs={'cluster_id': cluster['id']}),
            headers=self.default_headers
        )
        deploy_uuid = json.loads(resp.body)['uuid']
        resp = self.app.delete(
            reverse(
                'ClusterHandler',
                kwargs={'cluster_id': cluster['id']}),
            headers=self.default_headers
        )
        timeout = 120
        timer = time.time()
        while True:
            task_deploy = self.db.query(Task).filter_by(
                uuid=deploy_uuid
            ).first()
            task_delete = self.db.query(Task).filter_by(
                cluster_id=cluster['id'],
                name="cluster_deletion"
            ).first()
            if not task_delete:
                break
            self.db.expire(task_deploy)
            self.db.expire(task_delete)
            if (time.time() - timer) > timeout:
                break
            time.sleep(1)

        cluster_db = self.db.query(Cluster).get(cluster['id'])
        self.assertIsNone(cluster_db)

    @patch('nailgun.task.task.rpc.cast', nailgun.task.task.fake_cast)
    @patch('nailgun.task.task.settings.FAKE_TASKS', True)
    def test_node_fqdn_is_assigned(self):
        cluster = self.create_cluster_api()
        node1 = self.create_default_node(cluster_id=cluster['id'],
                                         pending_addition=True)
        node2 = self.create_default_node(cluster_id=cluster['id'],
                                         pending_addition=True)
        resp = self.app.put(
            reverse(
                'ClusterChangesHandler',
                kwargs={'cluster_id': cluster['id']}),
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
        nodes = self.db.query(Node).all()
        for node in (node1, node2):
            self.db.refresh(node)
            fqdn = "slave-%s.%s" % (node.id, settings.DNS_DOMAIN)
            self.assertEquals(fqdn, node.fqdn)
