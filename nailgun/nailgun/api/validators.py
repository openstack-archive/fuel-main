# -*- coding: utf-8 -*-

import json
import types

import web

from nailgun.db import orm
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
    def validate_json(cls, data):
        if data:
            try:
                res = json.loads(data)
            except:
                raise web.webapi.badrequest(
                    message="Invalid json format"
                )
        else:
            raise web.webapi.badrequest(
                message="Empty request received"
            )
        return res

    @classmethod
    def validate(cls, data):
        raise NotImplementedError("You should override this method")


class MetaInterfacesValidator(BasicValidator):
    @classmethod
    def validate(cls, interfaces):
        if not isinstance(interfaces, list):
            raise web.webapi.badrequest(
                message="Meta.interfaces should be list"
            )
        for nic in interfaces:
            for key in ('mac', 'name'):
                if key in nic and isinstance(nic[key], basestring) and\
                        nic[key]:
                    continue
                raise web.webapi.badrequest(
                    message="Interface in meta.interfaces should have"
                            " key %r with nonempty string value" % key
                )
            for key in ('max_speed', 'current_speed'):
                if key not in nic or isinstance(nic[key], types.NoneType) or\
                        (isinstance(nic[key], int) and nic[key] >= 0):
                    continue
                raise web.webapi.badrequest(
                    message="Interface in meta.interfaces should have key %r"
                            " with positive integer or Null value" % key
                )


class MetaValidator(BasicValidator):
    @classmethod
    def validate(cls, meta):
        if not isinstance(meta, dict):
            raise web.webapi.badrequest(message="Meta should be dict")
        if 'interfaces' in meta:
            MetaInterfacesValidator.validate(meta['interfaces'])


class ReleaseValidator(BasicValidator):

    @classmethod
    def validate(cls, data):
        d = cls.validate_json(data)
        if not "name" in d:
            raise web.webapi.badrequest(
                message="No release name specified"
            )
        if not "version" in d:
            raise web.webapi.badrequest(
                message="No release version specified"
            )
        if orm().query(Release).filter_by(
            name=d["name"],
            version=d["version"]
        ).first():
            raise web.webapi.conflict
        if "networks_metadata" in d:
            for network in d["networks_metadata"]:
                if not "name" in network or not "access" in network:
                    raise web.webapi.badrequest(
                        message="Invalid network data: %s" % str(network)
                    )
                if network["access"] not in settings.NETWORK_POOLS:
                    raise web.webapi.badrequest(
                        message="Invalid access mode for network"
                    )
        else:
            d["networks_metadata"] = []
        if not "attributes_metadata" in d:
            d["attributes_metadata"] = {}
        else:
            try:
                Attributes.validate_fixture(d["attributes_metadata"])
            except:
                raise web.webapi.badrequest(
                    message="Invalid logical structure of attributes metadata"
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
                c = web.webapi.conflict
                c.message = "Environment with this name already exists"
                raise c()
        if d.get("release"):
            release = orm().query(Release).get(d.get("release"))
            if not release:
                raise web.webapi.badrequest(message="Invalid release id")
        return d


class AttributesValidator(BasicValidator):
    @classmethod
    def validate(cls, data):
        d = cls.validate_json(data)
        if "generated" in d:
            raise web.webapi.badrequest(
                message="It is not allowed to update generated attributes"
            )
        if "editable" in d and not isinstance(d["editable"], dict):
            raise web.webapi.badrequest(
                message="Editable attributes should be a dictionary"
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
        d = cls.validate_json(data)
        if not d:
            raise web.webapi.badrequest(
                message="No valid data received"
            )
        if not "mac" in d:
            raise web.webapi.badrequest(
                message="No mac address specified"
            )
        else:
            q = orm().query(Node)
            if q.filter(Node.mac == d["mac"]).first():
                raise web.webapi.conflict()
            if cls.validate_existent_node_mac(d):
                raise web.webapi.conflict()
        if "id" in d:
            raise web.webapi.badrequest(
                message="Manual ID setting is prohibited"
            )
        if 'meta' in d:
            MetaValidator.validate(d['meta'])
        return d

    @classmethod
    def validate_existent_node_mac(cls, data):
        if 'meta' in data:
            MetaValidator.validate(data['meta'])
            if 'interfaces' in data['meta']:
                existent_node = orm().query(Node).filter(Node.mac.in_(
                    [n['mac'] for n in data['meta']['interfaces']])).first()
                return existent_node

    @classmethod
    def validate_update(cls, data):
        d = cls.validate_json(data)
        if not d:
            raise web.webapi.badrequest(
                message="No valid data received"
            )
        if "status" in d and d["status"] not in Node.NODE_STATUSES:
            raise web.webapi.badrequest(
                message="Invalid status for node"
            )
        if "id" in d:
            raise web.webapi.badrequest(
                message="Manual ID setting is prohibited"
            )
        if 'meta' in d:
            MetaValidator.validate(d['meta'])
        return d

    @classmethod
    def validate_collection_update(cls, data):
        d = cls.validate_json(data)
        if not isinstance(d, list):
            raise web.badrequest(
                "Invalid json list"
            )

        q = orm().query(Node)
        for nd in d:
            if not "mac" in nd and not "id" in nd:
                raise web.badrequest(
                    "MAC or ID is not specified"
                )
            else:
                if "mac" in nd:
                    existent_node = q.filter_by(mac=nd["mac"]).first() \
                        or cls.validate_existent_node_mac(nd)
                    if not existent_node:
                        raise web.badrequest(
                            "Invalid MAC specified"
                        )
                if "id" in nd and not q.get(nd["id"]):
                    raise web.badrequest(
                        "Invalid ID specified"
                    )
            if 'meta' in nd:
                MetaValidator.validate(nd['meta'])
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
            raise web.webapi.badrequest("Bad status")

        return valid

    @classmethod
    def validate_collection_update(cls, data):
        d = cls.validate_json(data)
        if not isinstance(d, list):
            raise web.badrequest(
                "Invalid json list"
            )

        q = orm().query(Notification)
        valid_d = []
        for nd in d:
            valid_nd = {}
            if "id" not in nd:
                raise web.badrequest("ID is not set correctly")

            if "status" not in nd:
                raise web.badrequest("ID is not set correctly")

            if not q.get(nd["id"]):
                raise web.badrequest("Invalid ID specified")

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
            raise web.webapi.badrequest(
                message="No valid data received"
            )
        if not isinstance(networks, list):
            raise web.webapi.badrequest(
                message="It's expected to receive array, not a single object"
            )
        for i in networks:
            if not 'id' in i:
                raise web.webapi.badrequest(
                    message="No 'id' param for '{0}'".format(i)
                )

            if i.get('name') == 'public':
                try:
                    IPNetwork('0.0.0.0/' + i['netmask'])
                except (AddrFormatError, KeyError):
                    raise web.webapi.badrequest(
                        message="Invalid netmask for public network")
        return d


class NetAssignmentValidator(BasicValidator):
    @classmethod
    def validate(cls, node):
        if not isinstance(node, dict):
            raise web.webapi.badrequest(message="Each node should be dict")
        if 'id' not in node:
            raise web.webapi.badrequest(message="Each node should have ID")
        if 'interfaces' not in node or \
                not isinstance(node['interfaces'], list):
            raise web.webapi.badrequest(
                message="There is no 'interfaces' list in node '%d'" %
                        node['id']
            )

        net_ids = set()
        for iface in node['interfaces']:
            if not isinstance(iface, dict):
                raise web.webapi.badrequest(
                    message="Node '%d': each interface should be dict" %
                            node['id']
                )
            if 'id' not in iface:
                raise web.webapi.badrequest(
                    message="Node '%d': each interface should have ID" %
                            node['id']
                )
            if 'assigned_networks' not in iface or \
                    not isinstance(iface['assigned_networks'], list):
                raise web.webapi.badrequest(
                    message="There is no 'assigned_networks' list"
                            " in interface '%d' in node '%d'" %
                            (iface['id'], node['id'])
                )

            for net in iface['assigned_networks']:
                if not isinstance(net, dict):
                    raise web.webapi.badrequest(
                        message="Node '%d', interface '%d':"
                                " each assigned network should be dict" %
                                (iface['id'], node['id'])
                    )
                if 'id' not in net:
                    raise web.webapi.badrequest(
                        message="Node '%d', interface '%d':"
                                " each assigned network should have ID" %
                                (iface['id'], node['id'])
                    )
                if net['id'] in net_ids:
                    raise web.webapi.badrequest(
                        message="Assigned networks for node '%d' have"
                                " a duplicate network '%d' (second"
                                " occurrence in interface '%d')" %
                                (node['id'], net['id'], iface['id'])
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
            raise web.webapi.badrequest(message="Data should be list of nodes")
        for node_data in data:
            cls.validate(node_data)
        return data

    @classmethod
    def verify_data_correctness(cls, node):
        db_node = orm().query(Node).filter_by(id=node['id']).first()
        if not db_node:
            raise web.webapi.badrequest(
                message="There is no node with ID '%d' in DB" % node['id']
            )
        interfaces = node['interfaces']
        db_interfaces = db_node.interfaces
        if len(interfaces) != len(db_interfaces):
            raise web.webapi.badrequest(
                message="Node '%d' has different amount of interfaces" %
                        node['id']
            )
        # FIXIT: we should use not all networks but appropriate for this
        # node only.
        db_network_groups = orm().query(NetworkGroup).filter_by(
            cluster_id=db_node.cluster_id
        ).all()
        if not db_network_groups:
            raise web.webapi.badrequest(
                message="There are no networks related to"
                        " node '%d' in DB" % node['id']
            )
        network_group_ids = set([ng.id for ng in db_network_groups])

        for iface in interfaces:
            db_iface = filter(
                lambda i: i.id == iface['id'],
                db_interfaces
            )
            if not db_iface:
                raise web.webapi.badrequest(
                    message="There is no interface with ID '%d'"
                            " for node '%d' in DB" %
                            (iface['id'], node['id'])
                )
            db_iface = db_iface[0]

            for net in iface['assigned_networks']:
                if net['id'] not in network_group_ids:
                    raise web.webapi.badrequest(
                        message="Node '%d' shouldn't be connected to"
                                " network with ID '%d'" %
                                (node['id'], net['id'])
                    )
                network_group_ids.remove(net['id'])

        # Check if there are unassigned networks for this node.
        if network_group_ids:
            raise web.webapi.badrequest(
                message="Too few neworks to assign to node '%d'" %
                        node['id']
            )
