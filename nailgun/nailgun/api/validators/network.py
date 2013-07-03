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

from netaddr import IPNetwork, AddrFormatError

from nailgun.db import db
from nailgun.errors import errors
from nailgun.api.models import Node, NetworkGroup
from nailgun.api.validators.base import BasicValidator


class NetworkConfigurationValidator(BasicValidator):
    @classmethod
    def validate_networks_update(cls, data):
        d = cls.validate_json(data)
        networks = d['networks']

        if not d:
            raise errors.InvalidData(
                "No valid data received",
                log_message=True
            )
        if not isinstance(networks, list):
            raise errors.InvalidData(
                "It's expected to receive array, not a single object",
                log_message=True
            )
        for i in networks:
            if not 'id' in i:
                raise errors.InvalidData(
                    "No 'id' param for '{0}'".format(i),
                    log_message=True
                )

            if i.get('name') == 'public':
                try:
                    IPNetwork('0.0.0.0/' + i['netmask'])
                except (AddrFormatError, KeyError):
                    raise errors.InvalidData(
                        "Invalid netmask for public network",
                        log_message=True
                    )
        return d


class NetAssignmentValidator(BasicValidator):
    @classmethod
    def validate(cls, node):
        if not isinstance(node, dict):
            raise errors.InvalidData(
                "Each node should be dict",
                log_message=True
            )
        if 'id' not in node:
            raise errors.InvalidData(
                "Each node should have ID",
                log_message=True
            )
        if 'interfaces' not in node or \
                not isinstance(node['interfaces'], list):
            raise errors.InvalidData(
                "There is no 'interfaces' list in node '%d'" % node['id'],
                log_message=True
            )

        net_ids = set()
        for iface in node['interfaces']:
            if not isinstance(iface, dict):
                raise errors.InvalidData(
                    "Node '%d': each interface should be dict (got '%s')" % (
                        node['id'],
                        str(iface)
                    ),
                    log_message=True
                )
            if 'id' not in iface:
                raise errors.InvalidData(
                    "Node '%d': each interface should have ID" % node['id'],
                    log_message=True
                )
            if 'assigned_networks' not in iface or \
                    not isinstance(iface['assigned_networks'], list):
                raise errors.InvalidData(
                    "There is no 'assigned_networks' list"
                    " in interface '%d' in node '%d'" %
                    (iface['id'], node['id']),
                    log_message=True
                )

            for net in iface['assigned_networks']:
                if not isinstance(net, dict):
                    raise errors.InvalidData(
                        "Node '%d', interface '%d':"
                        " each assigned network should be dict" %
                        (iface['id'], node['id']),
                        log_message=True
                    )
                if 'id' not in net:
                    raise errors.InvalidData(
                        "Node '%d', interface '%d':"
                        " each assigned network should have ID" %
                        (iface['id'], node['id']),
                        log_message=True
                    )
                if net['id'] in net_ids:
                    raise errors.InvalidData(
                        "Assigned networks for node '%d' have"
                        " a duplicate network '%d' (second"
                        " occurrence in interface '%d')" %
                        (node['id'], net['id'], iface['id']),
                        log_message=True
                    )
                net_ids.add(net['id'])
        return node

    @classmethod
    def validate_structure(cls, webdata):
        node_data = cls.validate_json(webdata)
        return cls.validate(node_data)

    @classmethod
    def validate_collection_structure(cls, webdata):
        data = cls.validate_json(webdata)
        if not isinstance(data, list):
            raise errors.InvalidData(
                "Data should be list of nodes",
                log_message=True
            )
        for node_data in data:
            cls.validate(node_data)
        return data

    @classmethod
    def verify_data_correctness(cls, node):
        db_node = db().query(Node).filter_by(id=node['id']).first()
        if not db_node:
            raise errors.InvalidData(
                "There is no node with ID '%d' in DB" % node['id'],
                log_message=True
            )
        interfaces = node['interfaces']
        db_interfaces = db_node.interfaces
        if len(interfaces) != len(db_interfaces):
            raise errors.InvalidData(
                "Node '%d' has different amount of interfaces" % node['id'],
                log_message=True
            )
        # FIXIT: we should use not all networks but appropriate for this
        # node only.
        db_network_groups = db().query(NetworkGroup).filter_by(
            cluster_id=db_node.cluster_id
        ).all()
        if not db_network_groups:
            raise errors.InvalidData(
                "There are no networks related to"
                " node '%d' in DB" % node['id'],
                log_message=True
            )
        network_group_ids = set([ng.id for ng in db_network_groups])

        for iface in interfaces:
            db_iface = filter(
                lambda i: i.id == iface['id'],
                db_interfaces
            )
            if not db_iface:
                raise errors.InvalidData(
                    "There is no interface with ID '%d'"
                    " for node '%d' in DB" %
                    (iface['id'], node['id']),
                    log_message=True
                )
            db_iface = db_iface[0]

            for net in iface['assigned_networks']:
                if net['id'] not in network_group_ids:
                    raise errors.InvalidData(
                        "Node '%d' shouldn't be connected to"
                        " network with ID '%d'" %
                        (node['id'], net['id']),
                        log_message=True
                    )
                network_group_ids.remove(net['id'])

        # Check if there are unassigned networks for this node.
        if network_group_ids:
            raise errors.InvalidData(
                "Too few networks to assign to node '%d'" % node['id'],
                log_message=True
            )
