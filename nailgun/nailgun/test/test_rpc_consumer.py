# -*- coding: utf-8 -*-

import json
import time
import uuid

from mock import patch

import nailgun.rpc as rpc
from nailgun.rpc import receiver as rcvr
from nailgun.task.task import VerifyNetworksTask
from nailgun.test.base import BaseHandlers
from nailgun.test.base import reverse
from nailgun.api.models import Node
from nailgun.api.models import Task
from nailgun.api.models import Cluster
from nailgun.api.models import Notification
from nailgun.api.models import Attributes
from nailgun.api.models import Network
from nailgun.api.models import NetworkGroup
from nailgun.api.models import IPAddr
from nailgun.api.models import Vlan


class TestVerifyNetworks(BaseHandlers):

    def test_verify_networks_resp(self):
        self.env.create(
            cluster_kwargs={},
            nodes_kwargs=[
                {"api": False},
                {"api": False}
            ]
        )
        cluster_db = self.env.clusters[0]
        node1, node2 = self.env.nodes
        vlans = NetworkGroup.generate_vlan_ids_list(
            self.env.generate_ui_networks(cluster_db.id)
        )

        receiver = rcvr.NailgunReceiver()

        task = Task(
            name="verify_networks",
            cluster_id=cluster_db.id
        )
        task.cache = {
            "args": {
                "networks": [{'vlan_id': i} for i in xrange(100, 105)]
            }
        }
        self.db.add(task)
        self.db.commit()

        nets = [{'iface': 'eth0', 'vlans': xrange(100, 105)}]
        kwargs = {'task_uuid': task.uuid,
                  'status': 'ready',
                  'nodes': [{'uid': node1.id, 'networks': nets},
                            {'uid': node2.id, 'networks': nets}]}
        receiver.verify_networks_resp(**kwargs)
        self.db.refresh(task)
        self.assertEqual(task.status, "ready")
        self.assertEqual(task.message, None)

    def test_verify_networks_resp_error(self):
        self.env.create(
            cluster_kwargs={},
            nodes_kwargs=[
                {"api": False},
                {"api": False}
            ]
        )
        cluster_db = self.env.clusters[0]
        node1, node2 = self.env.nodes
        receiver = rcvr.NailgunReceiver()

        task = Task(
            name="super",
            cluster_id=cluster_db.id
        )
        task.cache = {
            "args": {
                "networks": [{'vlan_id': i} for i in xrange(100, 105)]
            }
        }
        self.db.add(task)
        self.db.commit()

        nets = [{'iface': 'eth0', 'vlans': range(100, 104)}]
        kwargs = {'task_uuid': task.uuid,
                  'status': 'ready',
                  'nodes': [{'uid': node1.id, 'networks': nets},
                            {'uid': node2.id, 'networks': nets}]}
        receiver.verify_networks_resp(**kwargs)
        self.db.refresh(task)
        self.assertEqual(task.status, "error")
        error_nodes = []
        for node in self.env.nodes:
            error_nodes.append({'uid': node.id, 'interface': 'eth0',
                                'name': node.name, 'absent_vlans': [104],
                                'mac': node.mac})
        self.assertEqual(task.message, None)
        self.assertEqual(task.result, error_nodes)

    def test_verify_networks_resp_error_with_removed_node(self):
        self.env.create(
            cluster_kwargs={},
            nodes_kwargs=[
                {"api": False},
                {"api": False}
            ]
        )

        receiver = rcvr.NailgunReceiver()
        cluster_db = self.env.clusters[0]
        node1, node2 = self.env.nodes

        task = Task(
            name="super",
            cluster_id=cluster_db.id
        )
        task.cache = {
            "args": {
                "networks": [{'vlan_id': i} for i in xrange(100, 105)]
            }
        }
        self.db.add(task)
        self.db.commit()

        nets = [{'iface': 'eth0', 'vlans': range(100, 104)}]
        kwargs = {'task_uuid': task.uuid,
                  'status': 'ready',
                  'nodes': [{'uid': node1.id, 'networks': nets},
                            {'uid': node2.id, 'networks': nets}]}
        self.db.delete(node2)
        self.db.commit()
        receiver.verify_networks_resp(**kwargs)
        resp = self.app.get(
            reverse('TaskHandler', kwargs={'task_id': task.id}),
            headers=self.default_headers
        )
        self.assertEquals(resp.status, 200)
        task = json.loads(resp.body)
        self.assertEqual(task['status'], "error")
        error_nodes = [{'uid': node1.id, 'interface': 'eth0',
                        'name': node1.name, 'absent_vlans': [104],
                        'mac': node1.mac},
                       {'uid': 2, 'interface': 'eth0',
                        'absent_vlans': [104]}]
        self.assertEqual(task.get('message'), None)
        self.assertEqual(task['result'], error_nodes)

    def test_verify_networks_resp_empty_nodes_default_error(self):
        self.env.create(
            cluster_kwargs={},
            nodes_kwargs=[
                {"api": False},
                {"api": False}
            ]
        )
        cluster_db = self.env.clusters[0]
        node1, node2 = self.env.nodes

        receiver = rcvr.NailgunReceiver()

        task = Task(
            name="super",
            cluster_id=cluster_db.id
        )
        task.cache = {
            "args": {
                "networks": [{'vlan_id': i} for i in xrange(100, 105)]
            }
        }
        self.db.add(task)
        self.db.commit()

        kwargs = {'task_uuid': task.uuid,
                  'status': 'ready',
                  'nodes': []}
        receiver.verify_networks_resp(**kwargs)
        self.db.refresh(task)
        self.assertEqual(task.status, "error")
        error_msg = 'Deployment Orchestrator failed to perform ' \
                    'network connectivity check. See logs for details.'
        self.assertEqual(task.message, error_msg)

    def test_verify_networks_resp_empty_nodes_custom_error(self):
        self.env.create(
            cluster_kwargs={},
            nodes_kwargs=[
                {"api": False},
                {"api": False}
            ]
        )
        cluster_db = self.env.clusters[0]
        node1, node2 = self.env.nodes

        receiver = rcvr.NailgunReceiver()

        task = Task(
            name="super",
            cluster_id=cluster_db.id
        )
        task.cache = {
            "args": {
                "networks": [{'vlan_id': i} for i in xrange(100, 105)]
            }
        }
        self.db.add(task)
        self.db.commit()

        error_msg = 'Custom error message.'
        kwargs = {'task_uuid': task.uuid,
                  'status': 'ready',
                  'nodes': [],
                  'error': error_msg}
        receiver.verify_networks_resp(**kwargs)
        self.db.refresh(task)
        self.assertEqual(task.status, "error")
        self.assertEqual(task.message, error_msg)


class TestConsumer(BaseHandlers):

    def test_node_deploy_resp(self):
        node = self.env.create_node(api=False)
        node2 = self.env.create_node(api=False)
        receiver = rcvr.NailgunReceiver()

        task = Task(
            uuid=str(uuid.uuid4()),
            name="deploy"
        )
        self.db.add(task)
        self.db.commit()

        kwargs = {'task_uuid': task.uuid,
                  'nodes': [{'uid': node.id, 'status': 'deploying'},
                            {'uid': node2.id, 'status': 'error'}]}
        receiver.deploy_resp(**kwargs)
        self.db.refresh(node)
        self.db.refresh(node2)
        self.db.refresh(task)
        self.assertEqual((node.status, node2.status), ("deploying", "error"))
        # it is running because we don't stop deployment
        # if there are error nodes
        self.assertEqual(task.status, "running")

    def test_task_progress(self):
        receiver = rcvr.NailgunReceiver()

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

    def test_error_node_progress(self):
        self.env.create(
            cluster_kwargs={},
            nodes_kwargs=[
                {"api": False}
            ]
        )
        task = Task(
            uuid=str(uuid.uuid4()),
            name="super",
            status="running"
        )
        self.db.add(task)
        self.db.commit()
        receiver = rcvr.NailgunReceiver()
        kwargs = {
            'task_uuid': task.uuid,
            'progress': 20,
            'nodes': [
                {
                    'uid': self.env.nodes[0].id,
                    'status': 'error',
                    'progress': 50
                }
            ]
        }
        receiver.deploy_resp(**kwargs)
        self.db.refresh(self.env.nodes[0])
        self.assertEqual(self.env.nodes[0].progress, 100)

    def test_remove_nodes_resp(self):
        self.env.create(
            cluster_kwargs={},
            nodes_kwargs=[
                {"api": False},
                {"api": False}
            ]
        )
        cluster_db = self.env.clusters[0]
        node1, node2 = self.env.nodes

        receiver = rcvr.NailgunReceiver()

        task = Task(
            uuid=str(uuid.uuid4()),
            name="super",
            cluster_id=cluster_db.id
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
        self.env.create(
            cluster_kwargs={},
            nodes_kwargs=[
                {"api": False},
                {"api": False}
            ]
        )
        cluster_db = self.env.clusters[0]
        node1, node2 = self.env.nodes

        receiver = rcvr.NailgunReceiver()

        task = Task(
            uuid=str(uuid.uuid4()),
            name="super",
            cluster_id=cluster_db.id
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

    def test_remove_cluster_resp(self):
        self.env.create(
            cluster_kwargs={},
            nodes_kwargs=[
                {"api": False},
                {"api": False}
            ]
        )
        cluster_id = self.env.clusters[0].id
        node1, node2 = self.env.nodes
        node1_id, node2_id = [n.id for n in self.env.nodes]
        notification = self.env.create_notification(
            cluster_id=cluster_id
        )
        networks = self.db.query(Network)\
            .join(NetworkGroup).\
            filter(NetworkGroup.cluster_id == cluster_id).all()

        vlans = []
        for net in networks:
            vlans.append(net.vlan_id)

        receiver = rcvr.NailgunReceiver()

        task = Task(
            uuid=str(uuid.uuid4()),
            name="cluster_deletion",
            cluster_id=cluster_id
        )
        self.db.add(task)
        self.db.commit()

        kwargs = {'task_uuid': task.uuid,
                  'progress': 100,
                  'status': 'ready',
                  'nodes': [{'uid': node1.id},
                            {'uid': str(node2.id)}],
                  'error_nodes': []
                  }

        receiver.remove_cluster_resp(**kwargs)

        nodes_db = self.db.query(Node)\
            .filter_by(cluster_id=cluster_id).all()
        self.assertEquals(len(nodes_db), 0)

        ip_db = self.db.query(IPAddr)\
            .filter(IPAddr.node.in_([node1_id, node2_id])).all()
        self.assertEquals(len(ip_db), 0)

        vlan_db = self.db.query(Vlan)\
            .filter(Vlan.id.in_(vlans)).all()
        self.assertEquals(len(vlan_db), 0)

        attrs_db = self.db.query(Attributes)\
            .filter_by(cluster_id=cluster_id).all()
        self.assertEquals(len(attrs_db), 0)

        nots_db = self.db.query(Notification)\
            .filter_by(cluster_id=cluster_id).all()
        self.assertEquals(len(nots_db), 0)

        nets_db = self.db.query(Network)\
            .join(NetworkGroup).\
            filter(NetworkGroup.cluster_id == cluster_id).all()
        self.assertEquals(len(nets_db), 0)

        task_db = self.db.query(Task)\
            .filter_by(cluster_id=cluster_id).all()
        self.assertEquals(len(task_db), 0)

        cluster_db = self.db.query(Cluster).get(cluster_id)
        self.assertIsNone(cluster_db)

    def test_remove_cluster_resp_failed(self):
        self.env.create(
            cluster_kwargs={},
            nodes_kwargs=[
                {"api": False},
                {"api": False}
            ]
        )
        cluster_db = self.env.clusters[0]
        node1, node2 = self.env.nodes
        notification = self.env.create_notification(
            cluster_id=cluster_db.id
        )

        receiver = rcvr.NailgunReceiver()

        task = Task(
            uuid=str(uuid.uuid4()),
            name="cluster_deletion",
            cluster_id=cluster_db.id
        )
        self.db.add(task)
        self.db.commit()

        kwargs = {'task_uuid': task.uuid,
                  'progress': 100,
                  'status': 'error',
                  'nodes': [{'uid': node1.id}],
                  'error_nodes': [{'uid': node1.id,
                                   'error': "RPC method failed"}],
                  }

        receiver.remove_cluster_resp(**kwargs)
        self.db.refresh(task)
        self.assertEqual(task.status, "error")

        nodes_db = self.db.query(Node)\
            .filter_by(cluster_id=cluster_db.id).all()
        self.assertNotEqual(len(nodes_db), 0)

        attrs_db = self.db.query(Attributes)\
            .filter_by(cluster_id=cluster_db.id).all()
        self.assertNotEqual(len(attrs_db), 0)

        nots_db = self.db.query(Notification)\
            .filter_by(cluster_id=cluster_db.id).all()
        self.assertNotEqual(len(nots_db), 0)

        nets_db = self.db.query(Network)\
            .join(NetworkGroup).\
            filter(NetworkGroup.cluster_id == cluster_db.id).all()
        self.assertNotEqual(len(nets_db), 0)
