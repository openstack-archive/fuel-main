# -*- coding: utf-8 -*-
import json

from nailgun.api.models import Network, NetworkGroup
from nailgun.test.base import BaseHandlers
from nailgun.test.base import reverse
from nailgun.settings import settings


class TestHandlers(BaseHandlers):
    def test_nets_empty(self):
        resp = self.app.get(
            reverse('NetworkCollectionHandler'),
            headers=self.default_headers,
            expect_errors=True
        )
        self.assertEquals(404, resp.status)

    def test_valid_nets_returned_after_cluster_create(self):
        cluster = self.create_cluster_api()
        resp = self.app.get(
            reverse('NetworkCollectionHandler'),
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
        response = json.loads(resp.body)

        expected = [
            {
                'id': 1,
                'amount': 1,
                'name': u'floating',
                'cluster_id': cluster['id'],
                'vlan_start': 100,
                'cidr': '240.0.0.0/24',
                'network_size': 256
            },
            {
                'id': 2,
                'amount': 1,
                'name': u'fixed',
                'cluster_id': cluster['id'],
                'vlan_start': 101,
                'cidr': '10.0.0.0/24',
                'network_size': 256
            },
            {
                'id': 3,
                'amount': 1,
                'name': u'storage',
                'cluster_id': cluster['id'],
                'vlan_start': 102,
                'cidr': '192.168.0.0/24',
                'network_size': 256
            },
            {
                'id': 4,
                'amount': 1,
                'name': u'management',
                'cluster_id': cluster['id'],
                'vlan_start': 103,
                'cidr': '172.16.0.0/24',
                'network_size': 256
            },
            {
                'id': 5,
                'amount': 1,
                'name': u'public',
                'cluster_id': cluster['id'],
                'vlan_start': 104,
                'cidr': '240.0.1.0/24',
                'network_size': 256
            },
        ]
        self.assertEquals(expected, response)

    def test_get_networks_by_cluster_id(self):
        cluster1 = self.create_cluster_api()
        cluster2 = self.create_cluster_api()
        nets_len = len(
            self.db.query(Network).join(NetworkGroup).filter(
                NetworkGroup.cluster_id == cluster1['id']
            ).all()
        )

        resp = self.app.get(
            reverse('NetworkCollectionHandler'),
            params={'cluster_id': cluster1['id']},
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
        nets_received = json.loads(resp.body)
        self.assertEquals(nets_len, len(nets_received))
        self.assertEquals(cluster1['id'], nets_received[0]['cluster_id'])

    def test_network_group_update_changes_network(self):
        cluster = self.create_cluster_api()
        net1 = self.db.query(NetworkGroup).first()
        self.assertIsNotNone(net1)
        new_vlan_id = 500  # non-used vlan id
        new_nets = [{
            'id': net1.id,
            'vlan_start': new_vlan_id}]
        resp = self.app.put(
            reverse('NetworkCollectionHandler'),
            json.dumps(new_nets),
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
        self.db.refresh(net1)
        self.assertEquals(len(net1.networks), 1)
        self.assertEquals(net1.networks[0].vlan_id, 500)

    def test_networks_update_fails_with_wrong_net_id(self):
        new_nets = [{
            'id': 500,
            'vlan_id': 500}]
        resp = self.app.put(
            reverse('NetworkCollectionHandler'),
            json.dumps(new_nets),
            headers=self.default_headers,
            expect_errors=True
        )
        self.assertEquals(400, resp.status)
