#    Copyright 2013 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


# -*- coding: utf-8 -*-
import json

from sqlalchemy.sql import not_

from nailgun.api.models import Network, NetworkGroup
from nailgun.test.base import BaseHandlers
from nailgun.test.base import reverse
from nailgun.settings import settings
from nailgun.api.models import Cluster


class TestNetworkConfigurationHandler(BaseHandlers):
    def setUp(self):
        super(TestNetworkConfigurationHandler, self).setUp()
        cluster = self.env.create_cluster(api=True)
        self.cluster = self.db.query(Cluster).get(cluster['id'])

    def put(self, cluster_id, data, expect_errors=False):
        url = reverse(
            'NetworkConfigurationHandler',
            kwargs={'cluster_id': cluster_id})
        return self.app.put(
            url, json.dumps(data),
            headers=self.default_headers,
            expect_errors=expect_errors)

    def get(self, cluster_id, expect_errors=False):
        url = reverse(
            'NetworkConfigurationHandler',
            kwargs={'cluster_id': cluster_id})
        return self.app.get(
            url,
            headers=self.default_headers,
            expect_errors=expect_errors)

    def test_get_request_should_return_net_manager_and_networks(self):
        response = self.get(self.cluster.id)
        data = json.loads(response.body)
        cluster = self.db.query(Cluster).get(self.cluster.id)

        self.assertEquals(data['net_manager'], self.cluster.net_manager)
        for network_group in cluster.network_groups:
            network = [i for i in data['networks']
                       if i['id'] == network_group.id][0]

            keys = [
                'network_size',
                'name',
                'amount',
                'cluster_id',
                'vlan_start',
                'cidr',
                'id']

            for key in keys:
                self.assertEquals(network[key], getattr(network_group, key))

    def test_not_found_cluster(self):
        resp = self.get(self.cluster.id + 999, expect_errors=True)
        self.assertEquals(404, resp.status)

    def test_change_net_manager(self):
        new_net_manager = {'net_manager': 'VlanManager'}
        resp = self.put(self.cluster.id, new_net_manager)

        self.db.refresh(self.cluster)
        self.assertEquals(
            self.cluster.net_manager,
            new_net_manager['net_manager'])

    def test_do_not_update_net_manager_if_validation_is_failed(self):
        network = self.db.query(NetworkGroup).filter(
            not_(NetworkGroup.name == "fuelweb_admin")
        ).first()
        new_net_manager = {'net_manager': 'VlanManager',
                           'networks': [{'id': 500, 'vlan_start': 500}]}
        resp = self.put(self.cluster.id, new_net_manager, expect_errors=True)

        self.db.refresh(self.cluster)
        self.assertNotEquals(
            self.cluster.net_manager,
            new_net_manager['net_manager'])

    def test_network_group_update_changes_network(self):
        network = self.db.query(NetworkGroup).filter(
            not_(NetworkGroup.name == "fuelweb_admin")
        ).first()
        self.assertIsNotNone(network)
        new_vlan_id = 500  # non-used vlan id
        new_nets = {'networks': [{
            'id': network.id,
            'vlan_start': new_vlan_id}]}

        resp = self.put(self.cluster.id, new_nets)
        self.assertEquals(resp.status, 202)
        self.db.refresh(network)
        self.assertEquals(len(network.networks), 1)
        self.assertEquals(network.networks[0].vlan_id, 500)

    def test_update_networks_and_net_manager(self):
        network = self.db.query(NetworkGroup).filter(
            not_(NetworkGroup.name == "fuelweb_admin")
        ).first()
        new_vlan_id = 500  # non-used vlan id
        new_net = {'net_manager': 'VlanManager',
                   'networks': [{'id': network.id, 'vlan_start': new_vlan_id}]}
        resp = self.put(self.cluster.id, new_net)

        self.db.refresh(self.cluster)
        self.db.refresh(network)
        self.assertEquals(
            self.cluster.net_manager,
            new_net['net_manager'])
        self.assertEquals(network.networks[0].vlan_id, new_vlan_id)

    def test_networks_update_fails_with_wrong_net_id(self):
        new_nets = {'networks': [{
            'id': 500,
            'vlan_start': 500}]}

        resp = self.put(self.cluster.id, new_nets, expect_errors=True)
        self.assertEquals(202, resp.status)
        task = json.loads(resp.body)
        self.assertEquals(task['status'], 'error')
        self.assertEquals(
            task['message'],
            'Invalid network ID: 500'
        )
