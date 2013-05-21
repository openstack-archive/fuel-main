# -*- coding: utf-8 -*-
import unittest
import json

from nailgun.test.base import BaseHandlers
from nailgun.test.base import reverse
from nailgun.api.models import NetworkAssignment, AllowedNetworks, Cluster


class TestClusterHandlers(BaseHandlers):

    def test_assigned_networks_when_node_added(self):
        mac = '123'
        meta = {'interfaces': [
            {'name': 'eth0', 'mac': mac},
            {'name': 'eth1', 'mac': '654'},
        ]}
        node = self.env.create_node(api=True, meta=meta, mac=mac)
        cluster = self.env.create_cluster(api=True, nodes=[node['id']])
        resp = self.app.get(
            reverse('NodeNICsHandler', kwargs={'node_id': node['id']}),
            headers=self.default_headers)
        self.assertEquals(resp.status, 200)
        response = json.loads(resp.body)
        for resp_nic in response:
            if resp_nic['mac'] == mac:
                self.assertGreater(len(resp_nic['assigned_networks']), 0)
            else:
                self.assertEquals(resp_nic['assigned_networks'], [])

    def test_allowed_networks_when_node_added(self):
        mac = '123'
        meta = {'interfaces': [
            {'name': 'eth0', 'mac': mac},
            {'name': 'eth1', 'mac': 'abc'},
        ]}
        node = self.env.create_node(api=True, meta=meta, mac=mac)
        cluster = self.env.create_cluster(api=True, nodes=[node['id']])

        resp = self.app.get(
            reverse('NodeNICsHandler', kwargs={'node_id': node['id']}),
            headers=self.default_headers)
        self.assertEquals(resp.status, 200)
        response = json.loads(resp.body)
        for resp_nic in response:
            self.assertGreater(len(resp_nic['allowed_networks']), 0)

    def test_assignment_is_removed_when_delete_node_from_cluster(self):
        mac = '123'
        meta = {'interfaces': [
            {'name': 'eth0', 'mac': mac},
            {'name': 'eth1', 'mac': 'abc'},
        ]}
        node = self.env.create_node(api=True, meta=meta, mac=mac)
        cluster = self.env.create_cluster(api=True, nodes=[node['id']])
        resp = self.app.put(
            reverse('ClusterHandler', kwargs={'cluster_id': cluster['id']}),
            json.dumps({'nodes': []}),
            headers=self.default_headers
        )
        self.assertEquals(resp.status, 200)

        resp = self.app.get(
            reverse('NodeNICsHandler', kwargs={'node_id': node['id']}),
            headers=self.default_headers)
        self.assertEquals(resp.status, 200)
        response = json.loads(resp.body)
        for resp_nic in response:
            self.assertEquals(resp_nic['assigned_networks'], [])
            self.assertEquals(resp_nic['allowed_networks'], [])

    def test_assignment_is_removed_when_delete_cluster(self):
        mac = '12364759'
        meta = {'interfaces': [
            {'name': 'eth0', 'mac': mac},
            {'name': 'eth1', 'mac': 'abc'},
        ]}
        node = self.env.create_node(api=True, meta=meta, mac=mac)
        cluster = self.env.create_cluster(api=True, nodes=[node['id']])
        cluster_db = self.db.query(Cluster).get(cluster['id'])
        self.db.delete(cluster_db)
        self.db.commit()

        net_assignment = self.db.query(NetworkAssignment).all()
        self.assertEquals(len(net_assignment), 0)
        allowed_nets = self.db.query(AllowedNetworks).all()
        self.assertEquals(len(allowed_nets), 0)


class TestNodeHandlers(BaseHandlers):

    def test_network_assignment_when_node_created_and_added(self):
        cluster = self.env.create_cluster(api=True)
        mac = '123'
        meta = {'interfaces': [
            {'name': 'eth0', 'mac': mac},
            {'name': 'eth1', 'mac': '654'},
        ]}
        node = self.env.create_node(api=True, meta=meta, mac=mac,
                                    cluster_id=cluster['id'])
        resp = self.app.get(
            reverse('NodeNICsHandler', kwargs={'node_id': node['id']}),
            headers=self.default_headers)
        self.assertEquals(resp.status, 200)
        response = json.loads(resp.body)
        for resp_nic in response:
            if resp_nic['mac'] == mac:
                self.assertGreater(len(resp_nic['assigned_networks']), 0)
            else:
                self.assertEquals(resp_nic['assigned_networks'], [])
            self.assertGreater(len(resp_nic['allowed_networks']), 0)

    def test_network_assignment_when_node_added(self):
        cluster = self.env.create_cluster(api=True)
        mac = '123'
        meta = {'interfaces': [
            {'name': 'eth0', 'mac': mac},
            {'name': 'eth1', 'mac': 'abc'},
        ]}
        node = self.env.create_node(api=True, meta=meta, mac=mac)
        resp = self.app.put(
            reverse('NodeCollectionHandler'),
            json.dumps([{'id': node['id'], 'cluster_id': cluster['id']}]),
            headers=self.default_headers
        )
        self.assertEquals(resp.status, 200)

        resp = self.app.get(
            reverse('NodeNICsHandler', kwargs={'node_id': node['id']}),
            headers=self.default_headers)
        self.assertEquals(resp.status, 200)
        response = json.loads(resp.body)
        for resp_nic in response:
            if resp_nic['mac'] == mac:
                self.assertGreater(len(resp_nic['assigned_networks']), 0)
            else:
                self.assertEquals(resp_nic['assigned_networks'], [])
            self.assertGreater(len(resp_nic['allowed_networks']), 0)

    def test_assignment_is_removed_when_delete_node_from_cluster(self):
        cluster = self.env.create_cluster(api=True)
        mac = '123'
        meta = {'interfaces': [
            {'name': 'eth0', 'mac': mac},
            {'name': 'eth1', 'mac': 'abc'},
        ]}
        node = self.env.create_node(api=True, meta=meta, mac=mac,
                                    cluster_id=cluster['id'])
        resp = self.app.put(
            reverse('NodeCollectionHandler'),
            json.dumps([{'id': node['id'], 'cluster_id': None}]),
            headers=self.default_headers
        )
        self.assertEquals(resp.status, 200)

        resp = self.app.get(
            reverse('NodeNICsHandler', kwargs={'node_id': node['id']}),
            headers=self.default_headers)
        self.assertEquals(resp.status, 200)
        response = json.loads(resp.body)
        for resp_nic in response:
            self.assertEquals(resp_nic['assigned_networks'], [])
            self.assertEquals(resp_nic['allowed_networks'], [])
