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

"""Provisioning serializers for orchestrator"""

import json

from nailgun.api.models import IPAddr
from nailgun.db import db
from nailgun.logger import logger
from nailgun.network.manager import NetworkManager
from nailgun.settings import settings
from nailgun.task.helpers import TaskHelper


class ProvisioningSerializer(object):
    """Provisioning serializer"""

    @classmethod
    def serialize(cls, cluster):
        """Serialize cluster for provisioning."""

        serialized_nodes = cls.serialize_nodes(cluster)

        return {
            'engine': {
                'url': settings.COBBLER_URL,
                'username': settings.COBBLER_USER,
                'password': settings.COBBLER_PASSWORD},
            'nodes': serialized_nodes}

    @classmethod
    def serialize_nodes(cls, cluster):
        """Serialize nodes."""
        nodes_to_provision = TaskHelper.nodes_to_provision(cluster)
        cluster_attrs = cluster.attributes.merged_attrs_values()

        serialized_nodes = []
        for node in nodes_to_provision:
            serialized_node = cls.serialize_node(cluster_attrs, node)
            serialized_nodes.append(serialized_node)

        return serialized_nodes

    @classmethod
    def serialize_node(cls, cluster_attrs, node):
        """Serialize a single node."""

        serialized_node = {
            'power_address': node.ip,
            'name': TaskHelper.make_slave_name(node.id),
            'hostname': node.fqdn,
            'power_pass': cls.get_power_pass(node),

            'profile': cluster_attrs['cobbler']['profile'],
            'power_type': 'ssh',
            'power_user': 'root',
            'name_servers': '\"%s\"' % settings.DNS_SERVERS,
            'name_servers_search': '\"%s\"' % settings.DNS_SEARCH,
            'netboot_enabled': '1',
            'ks_meta': {
                'ks_spaces': "\"%s\"" % json.dumps(
                    node.attributes.volumes).replace("\"", "\\\""),

                'puppet_auto_setup': 1,
                'puppet_master': settings.PUPPET_MASTER_HOST,
                'puppet_version': settings.PUPPET_VERSION,
                'puppet_enable': 0,
                'mco_auto_setup': 1,
                'install_log_2_syslog': 1,
                'mco_pskey': settings.MCO_PSKEY,
                'mco_vhost': settings.MCO_VHOST,
                'mco_host': settings.MCO_HOST,
                'mco_user': settings.MCO_USER,
                'mco_password': settings.MCO_PASSWORD,
                'mco_connector': settings.MCO_CONNECTOR,
                'mco_enable': 1,
                'auth_key': "\"%s\"" % cluster_attrs.get('auth_key', '')}}

        serialized_node.update(cls.serialize_interfaces(node))

        return serialized_node

    @classmethod
    def serialize_interfaces(cls, node):
        interfaces = {}
        interfaces_extra = {}
        admin_ips = cls.get_admin_ips(node)

        for interface in node.meta.get('interfaces', []):
            name = interface['name']

            interfaces[name] = {
                'mac_address': interface['mac'],
                'static': '0',
                'netmask': settings.ADMIN_NETWORK['netmask'],
                'ip_address': admin_ips.pop()}

            # interfaces_extra field in cobbler ks_meta
            # means some extra data for network interfaces
            # configuration. It is used by cobbler snippet.
            # For example, cobbler interface model does not
            # have 'peerdns' field, but we need this field
            # to be configured. So we use interfaces_extra
            # branch in order to set this unsupported field.
            interfaces_extra[name] = {
                'peerdns': 'no',
                'onboot': 'no'}

            # We want node to be able to PXE boot via any of its
            # interfaces. That is why we add all discovered
            # interfaces into cobbler system. But we want
            # assignted fqdn to be resolved into one IP address
            # because we don't completely support multiinterface
            # configuration yet.
            if interface['mac'] == node.mac:
                interfaces[name]['dns_name'] = node.fqdn
                interfaces_extra[name]['onboot'] = 'yes'

        return {
            'interfaces': interfaces,
            'interfaces_extra': interfaces_extra}

    @classmethod
    def get_admin_ips(cls, node):
        netmanager = NetworkManager()
        admin_net_id = netmanager.get_admin_network_id()
        admin_ips = set([
            i.ip_addr for i in db().query(IPAddr).
            filter_by(node=node.id).
            filter_by(network=admin_net_id)])

        return admin_ips

    @classmethod
    def get_power_pass(cls, node):
        """Assign power pass depend on node state."""
        if node.status == "discover":
            logger.info(
                u'Node %s seems booted with bootstrap image', node.full_name)
            return settings.PATH_TO_BOOTSTRAP_SSH_KEY

        logger.info(u'Node %s seems booted with real system', node.full_name)
        return settings.PATH_TO_SSH_KEY


def serialize(cluster):
    """Serialize cluster for provisioning."""
    cluster.prepare_for_provisioning()
    return ProvisioningSerializer.serialize(cluster)
