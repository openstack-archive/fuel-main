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


from nailgun.orchestrator.serializers import serialize
from nailgun.orchestrator.serializers import OrchestratorHASerializer
from nailgun.orchestrator.serializers import OrchestratorSerializer

from nailgun.test.base import BaseHandlers
from nailgun.db import db
from nailgun.network.manager import NetworkManager
import json
from nailgun.test.base import fake_tasks
from mock import Mock, patch
from nailgun.api.models import Cluster
from nailgun.api.models import Node
from nailgun.settings import settings


class OrchestratorSerializerTestBase(BaseHandlers):
    """Class containts helpers"""

    def filter_by_role(self, nodes, role):
        return filter(lambda node: node['role'] == role, nodes)

    def filter_by_uid(self, nodes, uid):
        return filter(lambda node: node['uid'] == uid, nodes)



class TestOrchestratorSerializerAllModes(OrchestratorSerializerTestBase):

    def test_nodes_list_two_roles(self):
        cluster = self.create_env('multinode')
        serialized_data = OrchestratorSerializer.serialize(cluster)

    def test_nodes_list_one_role(self):
        cluster = self.create_env('multinode')
        serialized_data = OrchestratorSerializer.serialize(cluster)



class TestOrchestratorSerializerMultinode(OrchestratorSerializerTestBase):

    def setUp(self):
        super(TestOrchestratorSerializerMultinode, self).setUp()
        self.cluster = self.create_env('multinode')

    def create_env(self, mode):
        cluster = self.env.create(
            cluster_kwargs={
                'mode': mode,
            },
            nodes_kwargs=[
                {'roles': ['controller', 'cinder'], 'pending_addition': True},
                {'roles': ['compute', 'cinder'], 'pending_addition': True},
                {'roles': ['compute'], 'pending_addition': True},
                {'roles': ['cinder'], 'pending_addition': True}])

        cluster_db = self.db.query(Cluster).get(cluster['id'])
        cluster_db.prepare_for_deployment()
        return cluster_db

    @property
    def serializer(self):
        return OrchestratorSerializer

    def test_node_list(self):
        node_list = self.serializer.node_list(self.cluster.nodes)

        # Check right nodes count with right roles
        self.assertEquals(len(node_list), 6)
        self.assertEquals(len(self.filter_by_role(node_list, 'controller')), 1)
        self.assertEquals(len(self.filter_by_role(node_list, 'compute')), 2)
        self.assertEquals(len(self.filter_by_role(node_list, 'cinder')), 3)

        # Check common attrs
        for node in node_list:
            node_db = self.db.query(Node).get(int(node['uid']))
            self.assertEquals(node['public_netmask'], '255.255.255.0')
            self.assertEquals(node['internal_netmask'], '255.255.255.0')
            self.assertEquals(node['storage_netmask'], '255.255.255.0')
            self.assertEquals(node['uid'], str(node_db.id))
            self.assertEquals(node['name'], 'node-%d' % node_db.id)
            self.assertEquals(node['fqdn'], 'node-%d.%s' %
                              (node_db.id, settings.DNS_DOMAIN))

        # Check uncommon attrs
        node_uids = sorted(set([n['uid'] for n in node_list]))
        expected_list = [
            {
                'roles': ['controller', 'cinder'],
                'attrs': {
                    'uid': node_uids[0],
                    'internal_address': '192.168.0.2',
                    'public_address': '172.16.1.2',
                    'storage_address': '192.168.1.2'}},
            {
                'roles': ['compute', 'cinder'],
                'attrs': {
                    'uid': node_uids[1],
                    'internal_address': '192.168.0.3',
                    'public_address': '172.16.1.3',
                    'storage_address': '192.168.1.3'}},
            {
                
                'roles': ['compute'],
                'attrs': {
                    'uid': node_uids[2],
                    'internal_address': '192.168.0.5',
                    'public_address': '172.16.1.5',
                    'storage_address': '192.168.1.5'}},
            {
                'roles': ['cinder'],
                'attrs': {
                    'uid': node_uids[3],
                    'internal_address': '192.168.0.4',
                    'public_address': '172.16.1.4',
                    'storage_address': '192.168.1.4'}}]

        for expected in expected_list:
            attrs = expected['attrs']

            for role in expected['roles']:
                nodes = self.filter_by_role(node_list, role)
                node = self.filter_by_uid(nodes, attrs['uid'])[0]

                self.assertEquals(attrs['internal_address'],
                                  node['internal_address'])
                self.assertEquals(attrs['public_address'],
                                  node['public_address'])
                self.assertEquals(attrs['storage_address'],
                                  node['storage_address'])


class TestOrchestratorHASerializer(OrchestratorSerializer):

    def test_multinode_serializer(self):
        self.env.create(
            cluster_kwargs={
                "mode": "multinode"
            },
            nodes_kwargs=[
                {"roles": ["controller"], "pending_addition": True},
                {"roles": ["compute"], "pending_addition": True},
                {"roles": ["cinder"], "pending_addition": True},
            ]
        )
        cluster_db = self.env.clusters[0]


        netmanager = NetworkManager()
        nodes_ids = [n.id for n in cluster_db.nodes]
        if nodes_ids:
            netmanager.assign_ips(nodes_ids, "management")
            netmanager.assign_ips(nodes_ids, "public")
            netmanager.assign_ips(nodes_ids, "storage")

        print json.dumps(serialize(cluster_db), indent=4)


    @fake_tasks(fake_rpc=False, mock_rpc=False)
    @patch('nailgun.rpc.cast')
    def test_ha_serializer(self, mocked_rpc):
        self.env.create(
            cluster_kwargs={
                "mode": "ha_full",
            },
            nodes_kwargs=[
                {"role": "controller", "pending_addition": True},
                {"role": "controller", "pending_addition": True},
                {"role": "controller", "pending_addition": True},
                {"role": "compute", "pending_addition": True},
                {"role": "cinder", "pending_addition": True},

                {"role": "compute", "pending_addition": True},
                {"role": "quantum", "pending_addition": True},
                {"role": "swift-proxy", "pending_addition": True},
                {"role": "primary-swift-proxy", "pending_addition": True},
                {"role": "primary-controller", "pending_addition": True},
            ]
        )
        cluster_db = self.env.clusters[0]


        netmanager = NetworkManager()
        nodes_ids = [n.id for n in cluster_db.nodes]
        if nodes_ids:
            netmanager.assign_ips(nodes_ids, "management")
            netmanager.assign_ips(nodes_ids, "public")
            netmanager.assign_ips(nodes_ids, "storage")

        print json.dumps(serialize(cluster_db), indent=4)

        task = self.env.launch_deployment()

