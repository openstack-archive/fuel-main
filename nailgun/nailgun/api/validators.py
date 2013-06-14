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
import types

import web

from nailgun.db import orm
from nailgun.errors import errors
from nailgun.logger import logger
from nailgun.settings import settings
from nailgun.api.models import Release
from nailgun.api.models import Cluster
from nailgun.api.models import ClusterChanges
from nailgun.api.models import Attributes
from nailgun.api.models import Node
from nailgun.api.models import NetworkGroup
from nailgun.api.models import Network
from nailgun.api.models import Notification
from nailgun.volumes.manager import VolumeManager
from netaddr import IPNetwork, AddrFormatError


class BasicValidator(object):
    @classmethod
    def validate_json(cls, data, desired_type=None, client=None):
        if data:
            try:
                res = json.loads(data)
            except:
                raise errors.InvalidData(
                    "Invalid json received",
                    log_message=True
                )
            if desired_type and not isinstance(res, desired_type):
                raise errors.InvalidData(
                    "Invalid data received (expected {0})".format(
                        str(desired_type)
                    ),
                    log_message=True
                )
        else:
            raise errors.InvalidData(
                "Empty request received",
                log_message=True
            )
        return res

    @classmethod
    def validate(cls, data):
        raise NotImplementedError("You should override this method")


class MetaInterfacesValidator(BasicValidator):
    @classmethod
    def _validate_data(cls, interfaces):
        if not isinstance(interfaces, list):
            raise errors.InvalidInterfacesInfo(
                "Meta.interfaces should be list",
                log_message=True
            )

        for nic in interfaces:
            for key in ("current_speed", "max_speed"):
                if key in nic:
                    val = nic[key]
                    if not val:
                        continue
                    elif not isinstance(val, int) or nic[key] < 0:
                        del nic[key]
        return interfaces

    @classmethod
    def validate_create(cls, interfaces):
        interfaces = cls._validate_data(interfaces)

        def filter_valid_nic(nic):
            for key in ('mac', 'name'):
                if not key in nic or not isinstance(nic[key], basestring)\
                        or not nic[key]:
                    return False
            return True

        return filter(filter_valid_nic, interfaces)

    @classmethod
    def validate_update(cls, interfaces):
        interfaces = cls._validate_data(interfaces)

        for nic in interfaces:
            for key in ('mac', 'name'):
                if not key in nic or not isinstance(nic[key], basestring)\
                        or not nic[key]:
                    raise errors.InvalidInterfacesInfo(
                        "Interface in meta.interfaces should have"
                        " key %r with nonempty string value" % key,
                        log_message=True
                    )

        return interfaces


class MetaValidator(BasicValidator):
    @classmethod
    def _validate_data(cls, meta):
        if not isinstance(meta, dict):
            raise errors.InvalidMetadata(
                "Invalid data: 'meta' should be dict",
                log_message=True
            )

    @classmethod
    def validate_create(cls, meta):
        cls._validate_data(meta)
        if 'interfaces' in meta:
            meta['interfaces'] = MetaInterfacesValidator.validate_create(
                meta['interfaces']
            )
        else:
            raise errors.InvalidInterfacesInfo(
                "Failed to discover node: "
                "invalid interfaces info",
                log_message=True
            )
        return meta

    @classmethod
    def validate_update(cls, meta):
        cls._validate_data(meta)
        if 'interfaces' in meta:
            meta['interfaces'] = MetaInterfacesValidator.validate_update(
                meta['interfaces']
            )
        return meta


class ReleaseValidator(BasicValidator):

    @classmethod
    def validate(cls, data):
        d = cls.validate_json(data)
        if not "name" in d:
            raise errors.InvalidData(
                "No release name specified",
                log_message=True
            )
        if not "version" in d:
            raise errors.InvalidData(
                "No release version specified",
                log_message=True
            )
        if orm().query(Release).filter_by(
            name=d["name"],
            version=d["version"]
        ).first():
            raise errors.AlreadyExists(
                "Release with the same name and version "
                "already exists",
                log_message=True
            )
        if "networks_metadata" in d:
            for network in d["networks_metadata"]:
                if not "name" in network or not "access" in network:
                    raise errors.InvalidData(
                        "Invalid network data: %s" % str(network),
                        log_message=True
                    )
                if network["access"] not in settings.NETWORK_POOLS:
                    raise errors.InvalidData(
                        "Invalid access mode for network",
                        log_message=True
                    )
        else:
            d["networks_metadata"] = []
        if not "attributes_metadata" in d:
            d["attributes_metadata"] = {}
        else:
            try:
                Attributes.validate_fixture(d["attributes_metadata"])
            except:
                raise errors.InvalidData(
                    "Invalid logical structure of attributes metadata",
                    log_message=True
                )
        return d


class ClusterValidator(BasicValidator):
    @classmethod
    def validate(cls, data):
        d = cls.validate_json(data)
        if d.get("name"):
            if orm().query(Cluster).filter_by(
                name=d["name"]
            ).first():
                raise errors.AlreadyExists(
                    "Environment with this name already exists",
                    log_message=True
                )
        if d.get("release"):
            release = orm().query(Release).get(d.get("release"))
            if not release:
                raise errors.InvalidData(
                    "Invalid release id",
                    log_message=True
                )
        return d


class AttributesValidator(BasicValidator):
    @classmethod
    def validate(cls, data):
        d = cls.validate_json(data)
        if "generated" in d:
            raise errors.InvalidData(
                "It is not allowed to update generated attributes",
                log_message=True
            )
        if "editable" in d and not isinstance(d["editable"], dict):
            raise errors.InvalidData(
                "Editable attributes should be a dictionary",
                log_message=True
            )
        return d

    @classmethod
    def validate_fixture(cls, data):
        """
        Here we just want to be sure that data is logically valid.
        We try to generate "generated" parameters. If there will not
        be any error during generating then we assume data is
        logically valid.
        """
        d = cls.validate_json(data)
        if "generated" in d:
            cls.traverse(d["generated"])


class NodeValidator(BasicValidator):
    @classmethod
    def validate(cls, data):
        d = cls.validate_json(data, dict)
        if not "mac" in d:
            raise errors.InvalidData(
                "No mac address specified",
                log_message=True
            )
        else:
            q = orm().query(Node)
            if q.filter(Node.mac == d["mac"]).first():
                raise errors.AlreadyExists(
                    "Node with mac {0} already "
                    "exists - doing nothing".format(d["mac"]),
                    log_level="info"
                )
            if cls.validate_existent_node_mac_post(d):
                raise errors.AlreadyExists(
                    "Node with mac {0} already "
                    "exists - doing nothing".format(d["mac"]),
                    log_level="info"
                )
        if "id" in d:
            del d["id"]
        if 'meta' in d:
            MetaValidator.validate_create(d['meta'])
        return d

    # TODO: fix this using DRY
    @classmethod
    def validate_existent_node_mac_post(cls, data):
        if 'meta' in data:
            data['meta'] = MetaValidator.validate_create(data['meta'])
            if 'interfaces' in data['meta']:
                existent_node = orm().query(Node).filter(Node.mac.in_(
                    [n['mac'] for n in data['meta']['interfaces']])).first()
                return existent_node

    @classmethod
    def validate_existent_node_mac_put(cls, data):
        if 'meta' in data:
            data['meta'] = MetaValidator.validate_update(data['meta'])
            if 'interfaces' in data['meta']:
                existent_node = orm().query(Node).filter(Node.mac.in_(
                    [n['mac'] for n in data['meta']['interfaces']])).first()
                return existent_node

    @classmethod
    def validate_update(cls, data):
        d = cls.validate_json(data)
        if "status" in d and d["status"] not in Node.NODE_STATUSES:
            raise errors.InvalidData(
                "Invalid status for node",
                log_message=True
            )
        if "id" in d:
            del d["id"]
        if 'meta' in d:
            d['meta'] = MetaValidator.validate_update(d['meta'])
        return d

    @classmethod
    def validate_collection_update(cls, data):
        d = cls.validate_json(data)
        if not isinstance(d, list):
            raise errors.InvalidData(
                "Invalid json list",
                log_message=True
            )

        q = orm().query(Node)
        for nd in d:
            if not "mac" in nd and not "id" in nd:
                raise errors.InvalidData(
                    "MAC or ID is not specified",
                    log_message=True
                )
            else:
                if "mac" in nd:
                    existent_node = q.filter_by(mac=nd["mac"]).first() \
                        or cls.validate_existent_node_mac_put(nd)
                    if not existent_node:
                        raise errors.InvalidData(
                            "Invalid MAC specified",
                            log_message=True
                        )
                if "id" in nd and not q.get(nd["id"]):
                    raise errors.InvalidData(
                        "Invalid ID specified",
                        log_message=True
                    )
            if 'meta' in nd:
                nd['meta'] = MetaValidator.validate_update(nd['meta'])
        return d


class NodeAttributesValidator(BasicValidator):
    pass


class NodeVolumesValidator(BasicValidator):
    @classmethod
    def validate(cls, data):
        # Here we instantiate VolumeManager with data
        # and during initialization it validates volumes.
        # So we can get validated volumes just after
        # VolumeManager initialization
        vm = VolumeManager(data=data)
        return vm.volumes


class NotificationValidator(BasicValidator):
    @classmethod
    def validate_update(cls, data):

        valid = {}
        d = cls.validate_json(data)

        status = d.get("status", None)
        if status in Notification.NOTIFICATION_STATUSES:
            valid["status"] = status
        else:
            raise errors.InvalidData(
                "Bad status",
                log_message=True
            )

        return valid

    @classmethod
    def validate_collection_update(cls, data):
        d = cls.validate_json(data)
        if not isinstance(d, list):
            raise errors.InvalidData(
                "Invalid json list",
                log_message=True
            )

        q = orm().query(Notification)
        valid_d = []
        for nd in d:
            valid_nd = {}
            if "id" not in nd:
                raise errors.InvalidData(
                    "ID is not set correctly",
                    log_message=True
                )

            if "status" not in nd:
                raise errors.InvalidData(
                    "ID is not set correctly",
                    log_message=True
                )

            if not q.get(nd["id"]):
                raise errors.InvalidData(
                    "Invalid ID specified",
                    log_message=True
                )

            valid_nd["id"] = nd["id"]
            valid_nd["status"] = nd["status"]
            valid_d.append(valid_nd)
        return valid_d


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
                    "Node '%d': each interface should be dict" % node['id'],
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
        db_node = orm().query(Node).filter_by(id=node['id']).first()
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
        db_network_groups = orm().query(NetworkGroup).filter_by(
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
                "Too few neworks to assign to node '%d'" % node['id'],
                log_message=True
            )
