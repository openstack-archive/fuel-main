# -*- coding: utf-8 -*-

import time
import uuid

from mock import patch
import eventlet
eventlet.monkey_patch()

import nailgun.rpc as rpc
from nailgun.rpc import threaded
from nailgun.test.base import BaseHandlers
from nailgun.api.models import Node, Task


class TestConsumer(BaseHandlers):

    def test_node_deploy_resp(self):
        node = self.create_default_node()
        node2 = self.create_default_node()
        receiver = threaded.NailgunReceiver()

        task = Task(
            uuid=str(uuid.uuid4()),
            name="super"
        )
        self.db.add(task)
        self.db.commit()

        kwargs = {'task_uuid': task.uuid,
                  'nodes': [{'uid': node.id, 'status': 'deploying'},
                            {'uid': node2.id, 'status': 'error'}]}

        with patch('nailgun.rpc.threaded.notifier'):
            receiver.deploy_resp(**kwargs)

        self.db.refresh(node)
        self.db.refresh(node2)
        self.db.refresh(task)
        self.assertEqual((node.status, node2.status), ("deploying", "error"))
        self.assertEqual(task.status, "error")

    def test_verify_networks_resp(self):
        cluster = self.create_cluster_api()
        node1 = self.create_default_node(cluster_id=cluster['id'])
        node2 = self.create_default_node(cluster_id=cluster['id'])

        receiver = threaded.NailgunReceiver()

        task = Task(
            uuid=str(uuid.uuid4()),
            name="super",
            cluster_id=cluster['id']
        )
        self.db.add(task)
        self.db.commit()

        nets = [{'iface': 'eth0', 'vlans': range(100, 105)}]
        kwargs = {'task_uuid': task.uuid,
                  'status': 'ready',
                  'networks': [{'uid': node1.id, 'networks': nets},
                               {'uid': node2.id, 'networks': nets}]}
        receiver.verify_networks_resp(**kwargs)
        self.db.refresh(task)
        self.assertEqual(task.status, "ready")
        self.assertEqual(task.error, None)

    def test_verify_networks_resp_error(self):
        cluster = self.create_cluster_api()
        node1 = self.create_default_node(cluster_id=cluster['id'])
        node2 = self.create_default_node(cluster_id=cluster['id'])

        receiver = threaded.NailgunReceiver()

        task = Task(
            uuid=str(uuid.uuid4()),
            name="super",
            cluster_id=cluster['id']
        )
        self.db.add(task)
        self.db.commit()

        nets = [{'iface': 'eth0', 'vlans': range(100, 104)}]
        kwargs = {'task_uuid': task.uuid,
                  'status': 'ready',
                  'networks': [{'uid': node1.id, 'networks': nets},
                               {'uid': node2.id, 'networks': nets}]}
        receiver.verify_networks_resp(**kwargs)
        self.db.refresh(task)
        self.assertEqual(task.status, "error")
        error_nodes = [{'uid': node1.id, 'absent_vlans': [104]},
                       {'uid': node2.id, 'absent_vlans': [104]}]
        error_msg = "Following nodes do not have vlans:\n%s" % error_nodes
        self.assertEqual(task.error, error_msg)

    def test_task_progress(self):
        receiver = threaded.NailgunReceiver()

        task = Task(
            uuid=str(uuid.uuid4()),
            name="super",
            status="running"
        )
        self.db.add(task)
        self.db.commit()
        kwargs = {'task_uuid': task.uuid, 'progress': 20}
        receiver.deploy_resp(**kwargs)
        self.db.refresh(task)
        self.assertEqual(task.progress, 20)
        self.assertEqual(task.status, "running")

    def test_remove_nodes_resp(self):
        cluster = self.create_cluster_api()
        node1 = self.create_default_node(cluster_id=cluster['id'])
        node2 = self.create_default_node(cluster_id=cluster['id'])

        receiver = threaded.NailgunReceiver()

        task = Task(
            uuid=str(uuid.uuid4()),
            name="super",
            cluster_id=cluster['id']
        )
        self.db.add(task)
        self.db.commit()

        kwargs = {'task_uuid': task.uuid,
                  'progress': 100,
                  'status': 'ready',
                  'nodes': [{'uid': node1.id},
                            {'uid': str(node2.id)}]}

        receiver.remove_nodes_resp(**kwargs)
        self.db.refresh(task)
        self.assertEqual(task.status, "ready")
        nodes_db = self.db.query(Node).all()
        self.assertEquals(len(nodes_db), 0)

    def test_remove_nodes_resp_failure(self):
        cluster = self.create_cluster_api()
        node1 = self.create_default_node(cluster_id=cluster['id'])
        node2 = self.create_default_node(cluster_id=cluster['id'])

        receiver = threaded.NailgunReceiver()

        task = Task(
            uuid=str(uuid.uuid4()),
            name="super",
            cluster_id=cluster['id']
        )
        self.db.add(task)
        self.db.commit()

        kwargs = {'task_uuid': task.uuid,
                  'progress': 100,
                  'status': 'error',
                  'nodes': [],
                  'error_nodes': [{'uid': node1.id,
                                   'error': "RPC method failed"}]}

        receiver.remove_nodes_resp(**kwargs)
        self.db.refresh(task)
        self.assertEqual(task.status, "error")
        nodes_db = self.db.query(Node).all()
        error_node = self.db.query(Node).get(node1.id)
        self.db.refresh(error_node)
        self.assertEquals(len(nodes_db), 2)
        self.assertEquals(error_node.status, "error")
