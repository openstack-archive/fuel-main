# -*- coding: utf-8 -*-

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

import json
from netaddr import IPAddress, IPNetwork

from nailgun.test.base import BaseHandlers, reverse
from nailgun.api.models import Node
from nailgun.network.manager import NetworkManager
from nailgun.db import db
from nailgun.api.models import Network


class SubnetMatcher:
    '''
    Custom matcher. Returns True if ip address in network
    '''
    def __init__(self, subnet):
        self.subnet = subnet

    def __eq__(self, *args, **kwargs):
        net = args[0]
        if not IPAddress(net) in IPNetwork(self.subnet):
            return False

        return True


class TestOSTFHandler(BaseHandlers):

    def setUp(self):
        super(TestOSTFHandler, self).setUp()
        self.netmanager = NetworkManager()

    def get(self, cluster_id):
        url = reverse(
            'OSTFHandler',
            kwargs={'cluster_id': cluster_id})
        return self.app.get(url, headers=self.default_headers)

    def assing_ip_to_nodes(self):
        nodes_ids = [node.id for node in self.db.query(Node).all()]
        self.netmanager.assign_ips(nodes_ids, 'management')
        self.netmanager.assign_ips(nodes_ids, 'public')
        map(self.netmanager.assign_admin_ips, nodes_ids)

    def get_admin_network_cidr(self):
        return db().query(Network).filter_by(
            name="fuelweb_admin"
        ).first().cidr

    def test_get_multinode_mode(self):
        fqdn = 'fqdn.com'
        self.env.create(
            nodes_kwargs=[
                {'role': 'compute'},
                {'role': 'controller', 'fqdn': fqdn}])
        self.assing_ip_to_nodes()
        cluster_id = self.env.clusters[0].id

        result = json.loads(self.get(cluster_id).body)

        end_point_ip = self.netmanager.get_end_point_ip(cluster_id)
        subnet = self.get_admin_network_cidr()
        expected = {
            'controller_nodes_ips': [SubnetMatcher(subnet)],
            'horizon_url': 'http://%s/' % end_point_ip,
            'controller_nodes_names': [fqdn],
            'admin_tenant_name': 'admin',
            'admin_username': 'admin',
            'keystone_url': 'http://%s:5000/' % end_point_ip,
            'admin_password': 'admin'}

        self.assertDictContainsSubset(result, expected)

    def test_get_ha_mode(self):
        fqdns = ['fqdn1.com', 'fqdn2.com', 'fqdn3.com']
        self.env.create(
            cluster_kwargs={
                'mode': 'ha',
                'type': 'compute'},
            nodes_kwargs=[
                {'role': 'controller', 'fqdn': fqdns[0]},
                {'role': 'controller', 'fqdn': fqdns[1]},
                {'role': 'controller', 'fqdn': fqdns[2]}])

        self.assing_ip_to_nodes()

        cluster_id = self.env.clusters[0].id
        result = json.loads(self.get(cluster_id).body)
        end_point_ip = self.netmanager.get_end_point_ip(cluster_id)

        subnets = [self.get_admin_network_cidr() for _ in range(3)]
        expected = {
            'controller_nodes_ips': map(SubnetMatcher, subnets),
            'horizon_url': 'http://%s/' % end_point_ip,
            'controller_nodes_names': sorted(fqdns),
            'admin_tenant_name': 'admin',
            'admin_username': 'admin',
            'keystone_url': 'http://%s:5000/' % end_point_ip,
            'admin_password': 'admin'}

        self.assertDictContainsSubset(result, expected)
