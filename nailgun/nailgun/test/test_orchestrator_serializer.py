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


from nailgun.api.models import Cluster
from nailgun.api.models import IPAddrRange
from nailgun.api.models import NetworkGroup
from nailgun.api.models import Node
from nailgun.db import db
from nailgun.orchestrator.serializers import OrchestratorHASerializer
from nailgun.orchestrator.serializers import OrchestratorSerializer
from nailgun.settings import settings
from nailgun.test.base import BaseHandlers


class OrchestratorSerializerTestBase(BaseHandlers):
    """Class containts helpers."""

    def filter_by_role(self, nodes, role):
        return filter(lambda node: node['role'] == role, nodes)

    def filter_by_uid(self, nodes, uid):
        return filter(lambda node: node['uid'] == uid, nodes)

    def assert_nodes_with_role(self, nodes, role, count):
        self.assertEquals(len(self.filter_by_role(nodes, role)), count)

    def get_controllers(self, cluster_id):
        return db().query(Node).\
            filter_by(cluster_id=cluster_id,
                      pending_deletion=False).\
            filter(Node.role_list.any(name='controller')).\
            order_by(Node.id)


class TestOrchestratorSerializer(OrchestratorSerializerTestBase):

    def setUp(self):
        super(TestOrchestratorSerializer, self).setUp()
        self.cluster = self.create_env('multinode')

    def create_env(self, mode, network_manager='FlatDHCPManager'):
        cluster = self.env.create(
            cluster_kwargs={
                'mode': mode,
                'net_manager': network_manager
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

    def assert_roles_flattened(self, nodes):
        self.assertEquals(len(nodes), 6)
        self.assert_nodes_with_role(nodes, 'controller', 1)
        self.assert_nodes_with_role(nodes, 'compute', 2)
        self.assert_nodes_with_role(nodes, 'cinder', 3)

    def test_serialize_nodes(self):
        serialized_nodes = self.serializer.serialize_nodes(self.cluster.nodes)
        self.assert_roles_flattened(serialized_nodes)

        # Each not should be same as result of
        # serialize_node function
        for serialized_node in serialized_nodes:
            node_db = self.db.query(Node).get(int(serialized_node['uid']))

            expected_node = self.serializer.serialize_node(
                node_db, serialized_node['role'])
            self.assertEquals(serialized_node, expected_node)

    def test_serialize_node(self):
        node = self.env.create_node(
            api=True, cluster_id=self.cluster.id, pending_addition=True)
        self.cluster.prepare_for_deployment()

        node_db = self.db.query(Node).get(node['id'])

        serialized_data = self.serializer.serialize_node(node_db, 'controller')

        self.assertEquals(serialized_data['role'], 'controller')
        self.assertEquals(serialized_data['uid'], str(node_db.id))
        self.assertEquals(serialized_data['status'], node_db.status)
        self.assertEquals(serialized_data['online'], node_db.online)
        self.assertEquals(serialized_data['fqdn'],
                          'node-%d.%s' % (node_db.id, settings.DNS_DOMAIN))

    def test_node_list(self):
        node_list = self.serializer.node_list(self.cluster.nodes)

        # Check right nodes count with right roles
        self.assert_roles_flattened(node_list)

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
                    'internal_address': '192.168.0.4',
                    'public_address': '172.16.1.4',
                    'storage_address': '192.168.1.4'}},
            {
                'roles': ['cinder'],
                'attrs': {
                    'uid': node_uids[3],
                    'internal_address': '192.168.0.5',
                    'public_address': '172.16.1.5',
                    'storage_address': '192.168.1.5'}}]

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

    def test_controller_nodes(self):
        ctrl_nodes = self.serializer.controller_nodes(self.cluster.id)
        self.assertEquals(len(ctrl_nodes), 1)

        # And should equal to nodes in nodes_list
        all_nodes = self.serializer.node_list(self.cluster.nodes)
        ctrl_nodes_from_nodes_list = filter(
            lambda node: node['role'] == 'controller',
            all_nodes)

        self.assertEquals(ctrl_nodes, ctrl_nodes_from_nodes_list)

    def test_vlan_manager(self):
        cluster = self.create_env('multinode', 'VlanManager')
        facts = self.serializer.serialize(cluster)

        for fact in facts:
            self.assertEquals(fact['vlan_interface'], 'eth0')
            self.assertEquals(
                fact['novanetwork_parameters']['network_manager'],
                'VlanManager')
            self.assertEquals(
                fact['novanetwork_parameters']['num_networks'], 1)
            self.assertEquals(
                fact['novanetwork_parameters']['vlan_start'], 103)
            self.assertEquals(
                fact['novanetwork_parameters']['network_size'], 256)

    def test_floatin_ranges_generation(self):
        # Set ip ranges for floating ips
        ranges = [['172.16.0.2', '172.16.0.4'],
                  ['172.16.0.3', '172.16.0.5'],
                  ['172.16.0.10', '172.16.0.12']]

        floating_network_group = self.db.query(NetworkGroup).filter(
            NetworkGroup.name == 'floating').filter(
                NetworkGroup.cluster_id == self.cluster.id).first()

        # Remove floating ip addr ranges
        self.db.query(IPAddrRange).filter(
            IPAddrRange.network_group_id == floating_network_group.id).delete()

        # Add new ranges
        for ip_range in ranges:
            new_ip_range = IPAddrRange(
                first=ip_range[0],
                last=ip_range[1],
                network_group_id=floating_network_group.id)

            self.db.add(new_ip_range)
        self.db.commit()
        facts = self.serializer.serialize(self.cluster)

        for fact in facts:
            self.assertEquals(
                fact['floating_network_range'],
                ['172.16.0.2-172.16.0.4',
                 '172.16.0.3-172.16.0.5',
                 '172.16.0.10-172.16.0.12'])


class TestOrchestratorHASerializer(OrchestratorSerializerTestBase):

    def setUp(self):
        super(TestOrchestratorHASerializer, self).setUp()
        self.cluster = self.create_env('ha_compact')

    def create_env(self, mode):
        cluster = self.env.create(
            cluster_kwargs={
                'mode': mode,
            },
            nodes_kwargs=[
                {'roles': ['controller'], 'pending_addition': True},
                {'roles': ['controller'], 'pending_addition': True},
                {'roles': ['controller', 'cinder'], 'pending_addition': True},
                {'roles': ['compute', 'cinder'], 'pending_addition': True},
                {'roles': ['compute'], 'pending_addition': True},
                {'roles': ['cinder'], 'pending_addition': True}])

        cluster_db = self.db.query(Cluster).get(cluster['id'])
        cluster_db.prepare_for_deployment()
        return cluster_db

    @property
    def serializer(self):
        return OrchestratorHASerializer

    def test_node_list(self):
        serialized_nodes = self.serializer.node_list(self.cluster.nodes)

        for node in serialized_nodes:
            # Each node has swift_zone
            self.assertEquals(node['swift_zone'], node['uid'])

    def test_get_common_attrs(self):
        attrs = self.serializer.get_common_attrs(self.cluster)
        # vips
        self.assertEquals(attrs['management_vip'], '192.168.0.8')
        self.assertEquals(attrs['public_vip'], '172.16.1.8')

        # last_contrller
        controllers = self.get_controllers(self.cluster.id)
        self.assertEquals(attrs['last_controller'],
                          'node-%d' % controllers[-1].id)

        # primary_controller
        controllers = self.filter_by_role(attrs['nodes'], 'primary-controller')
        self.assertEquals(controllers[0]['role'], 'primary-controller')

        # mountpoints and mp attrs
        self.assertEquals(
            attrs['mp'],
            [{'point': '1', 'weight': '1'},
             {'point': '2', 'weight': '2'}])

        self.assertEquals(
            attrs['mountpoints'],
            '1 1\\n2 2\\n')
