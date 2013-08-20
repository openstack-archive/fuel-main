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


class OrchestratorSerializer(object):
    """
    Base class for orchestrator searilizatos
    """

    @classmethod
    def serialize(cls, cluster):
        attrs = cls.serialize_cluster_attrs(cluster)
        attrs['nodes'] = cls.serialize_nodes(cluster.nodes)
        return attrs

    @classmethod
    def serialize_cluster_attrs(cls, cluster_id):
        return {}

    @classmethod
    def serialize_nodes(cls, nodes):
        return map(cls.serialize_node, nodes)

    @classmethod
    def serialize_node(cls, node):
        network_data = node.network_data
        return {
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
            'network_data': cls.configure_interfaces(network_data)
        }

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
    def configure_interfaces(cls, network_data):
        interfaces = {}
        for network in network_data:
            # Set interface name
            if net.get('dev') and net.get('vlan'):
                name = '.'.join(net['dev'], net['vlan'])
            else:
                name = net['dev']

            

        if net['vlan'] && net['vlan'] != 0
          name = [net['dev'], net['vlan']].join('.')
        else
          name = net['dev']



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


class OrchestratorHAFullSerializer(OrchestratorSerializer):
    """
    Not implemented yet
    """
    pass
