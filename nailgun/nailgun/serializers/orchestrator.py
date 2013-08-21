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

"""
Serializers for orchestrator
"""

from netaddr import IPSet, IPNetwork, IPRange, IPAddress
from nailgun.task.helpers import TaskHelper
from sqlalchemy import and_
from nailgun.db import db
from nailgun.api.models import Node
from nailgun.api.models import Cluster
from nailgun.settings import settings
from nailgun.api.models import NetworkGroup


class OrchestratorSerializer(object):
    """
    Base class for orchestrator searilizatos
    """

    @classmethod
    def serialize(cls, cluster):
        attrs = cls.serialize_cluster_attrs(cluster)
        attrs['nodes'] = cls.serialize_nodes(
            cls.get_nodes_to_serialization(cluster))

        if cluster.net_manager == 'VlanManager':
            cls.add_vlan_interfaces(attrs['nodes'], cluster)

        return attrs

    @classmethod
    def get_nodes_to_serialization(cls, cluster):
        return db().query(Node).filter(
            and_(Node.cluster == cluster,
                 Node.pending_deletion == False)).order_by(Node.id)

    @classmethod
    def serialize_cluster_attrs(cls, cluster):
        attrs = cluster.attributes.merged_attrs_values()
        attrs['deployment_mode'] = cluster.mode
        attrs['deployment_id'] = cluster.id

        attrs['master_ip'] = settings.MASTER_IP
        attrs['controller_nodes'] = cls.controller_nodes(cluster.id)

        attrs.update(cls.network_ranges(cluster))
        attrs['novanetwork_attrs'] = cls.novanetwork_attrs(cluster)

        return attrs

    @classmethod
    def novanetwork_attrs(cls, cluster):
        attrs = {}
        attrs['network_manager'] = cluster.net_manager

        fixed_net = db().query(NetworkGroup).filter_by(
            cluster_id=cluster.id).filter_by(name='fixed').first()

        # network_size is required for all managers, otherwise
        # puppet will use default (255)
        attrs['network_size'] = fixed_net.network_size
        if attrs['network_manager'] == 'VlanManager':
            attrs['num_networks'] = fixed_net.amount
            attrs['vlan_start'] = fixed_net.vlan_start

        return attrs

    @classmethod
    def add_vlan_interfaces(cls, nodes):
        """
        We shouldn't pass to orchetrator fixed network
        when network manager is VlanManager, but we should specify
        fixed_interface (private_interface in terms of fuel) as result
        we just pass vlan_interface as node attribute.
        """
        netmanager = NetworkManager()
        for node in nodes:
            node_db = db().query(Node).get(node['id'])

            fixed_interface = netmanager._get_interface_by_network_name(
                node_db.id, 'fixed')

            node['vlan_interface'] = fixed_interface.name

    @classmethod
    def network_ranges(cls, cluster):
        ng_db = db().query(NetworkGroup).filter_by(cluster_id=cluster.id).all()
        attrs = {}
        for net in ng_db:
            net_name = net.name + '_network_range'

            if net.name == 'floating':
                attrs[net_name] = cls.get_ip_ranges_first_last(net)
            elif net.name == 'public':
                # We shouldn't pass public_network_range attribute
                continue
            else:
                attrs[net_name] = net.cidr

        return attrs

    @classmethod
    def get_ip_ranges_first_last(cls, network_group):
        """
        Get all ip ranges in "10.0.0.0-10.0.0.255" format
        """
        return [
            "{0}-{1}".format(ip_range.first, ip_range.last)
            for ip_range in network_group.ip_ranges
        ]

    @classmethod
    def controller_nodes(cls, cluster_id):
        nodes = db().query(Node).filter_by(
            cluster_id=cluster_id,
            role='controller',
            pending_deletion=False).order_by(Node.id)

        return cls.serialize_nodes(nodes)

    @classmethod
    def serialize_nodes(cls, nodes):
        return map(cls.serialize_node, nodes)

    @classmethod
    def serialize_node(cls, node):
        network_data = node.network_data
        interfaces = cls.configure_interfaces(network_data)
        cls.__add_hw_interfaces(interfaces, node.meta['interfaces'])
        node_attrs = {
            'uid': node.id,
            'fqdn': node.fqdn,
            'name': TaskHelper.make_slave_name(node.id, node.role),
            'role': node.role,
            'internal_address':  cls.get_addr(network_data, 'management')['ip'],
            'internal_netmask': cls.get_addr(network_data, 'management')['netmask'],
            'storage_address': cls.get_addr(network_data, 'storage')['ip'],
            'storage_netmask': cls.get_addr(network_data, 'storage')['netmask'],
            'public_address': cls.get_addr(network_data, 'public')['ip'],
            'public_netmask': cls.get_addr(network_data, 'public')['netmask'],

            # quantum?
            # 'default_gateway': n['default_gateway']

            # quantum
            # 'internal_br': n['internal_br'],

            # quantum
            # 'public_br': n['public_br'],
            'network_data': interfaces
        }
        node_attrs.update(cls.interfaces_list(network_data))

        return node_attrs

    @classmethod
    def get_addr(cls, network_data, name):
        net = filter(
            lambda net: net['name'] == name,
            network_data)[0]['ip']
        return {
            'ip': str(IPNetwork(net).ip),
            'netmask': str(IPNetwork(net).netmask)
        }

    @classmethod
    def interfaces_list(cls, network_data):
        interfaces = {}
        for network in network_data:
            interfaces['%s_interface' % network['name']] = \
                cls.__make_interface_name(
                    network.get('dev'),
                    network.get('vlan'))

        return interfaces

    @classmethod
    def configure_interfaces(cls, network_data):
        interfaces = {}
        for network in network_data:
            network_name = network['name']

            # floating and public are on the same interface
            # so, just skip floating
            if network_name == 'floating':
                continue

            name = cls.__make_interface_name(network.get('dev'), network.get('vlan'))
            interfaces[name] = {'interface': name, 'ipaddr': [], '_name': network_name}
            interface = interfaces[name]

            if network_name == 'admin':
                interface['ipaddr'] = 'dhcp'
            elif network.get('ip'):
                interface['ipaddr'].append(network.get('ip'))

            # Add gateway for public
            if network_name == 'public' and network.get('gateway'):
                interface['gateway'] = network['gateway']

            if len(interface['ipaddr']) == 0:
                interface['ipaddr'] = 'none'

        interfaces['lo'] = {'interface': 'lo', 'ipaddr': ['127.0.0.1/8']}

        return interfaces

    @classmethod
    def __make_interface_name(cls, name, vlan):
        if name and vlan:
            return '.'.join([name, str(vlan)])
        return name

    @classmethod
    def __add_hw_interfaces(cls, interfaces, hw_interfaces):
        for hw_interface in hw_interfaces:
            if not hw_interface['name'] in interfaces:
                interfaces[hw_interface['name']] = {
                    'interface': hw_interface['name'],
                    'ipaddr': []
                }


class OrchestratorMultinodeSerializer(OrchestratorSerializer):
    """
    Serialize cluster for multinode mode
    """
    def __init__(self, cluster_id):
        cluster_id
        mode

    def serialize(self):
        pass


class OrchestratorHACompactSerializer(OrchestratorSerializer):
    """
    Not implemented yet
    """
    pass

    # if task.cluster.mode == 'ha':
    # logger.info("HA mode chosen, creating VIP addresses for it..")
    # cluster_attrs['management_vip'] = netmanager.assign_vip(
    #     cluster_id, "management")
    # cluster_attrs['public_vip'] = netmanager.assign_vip(
    #     cluster_id, "public")


class OrchestratorHAFullSerializer(OrchestratorSerializer):
    """
    Not implemented yet
    """
    pass
