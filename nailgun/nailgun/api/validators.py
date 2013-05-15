# -*- coding: utf-8 -*-

import json

import web

from nailgun.db import orm
from nailgun.settings import settings
from nailgun.api.models import Release
from nailgun.api.models import Cluster
from nailgun.api.models import ClusterChanges
from nailgun.api.models import Attributes
from nailgun.api.models import Node
from nailgun.api.models import NetworkGroup
from nailgun.api.models import Network
from nailgun.api.models import Notification


class BasicValidator(object):
    db = orm()

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
        if cls.db.query(Release).filter_by(
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
        cls.db.expunge_all()
        return d


class ClusterValidator(BasicValidator):
    @classmethod
    def validate(cls, data):
        d = cls.validate_json(data)
        if d.get("name"):
            if cls.db.query(Cluster).filter_by(
                name=d["name"]
            ).first():
                c = web.webapi.conflict
                c.message = "Environment with this name already exists"
                raise c()
        if d.get("release"):
            release = cls.db.query(Release).get(d.get("release"))
            if not release:
                raise web.webapi.badrequest(message="Invalid release id")
        cls.db.expunge_all()
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
        if not "mac" in d:
            raise web.webapi.badrequest(
                message="No mac address specified"
            )
        else:
            q = cls.db.query(Node)
            if q.filter(Node.mac == d["mac"]).first():
                raise web.webapi.conflict()
            if cls.validate_existent_node_mac(d):
                raise web.webapi.conflict()
        if "id" in d:
            raise web.webapi.badrequest(
                message="Manual ID setting is prohibited"
            )
        cls.db.expunge_all()
        return d

    @classmethod
    def validate_existent_node_mac(cls, data):
        if 'meta' in data and 'interfaces' in data['meta']:
            existent_node = cls.db.query(Node).filter(Node.mac.in_(
                [n['mac'] for n in data['meta']['interfaces']])).first()
            cls.db.expunge_all()
            return existent_node

    @classmethod
    def validate_update(cls, data):
        d = cls.validate_json(data)
        if "status" in d and d["status"] not in Node.NODE_STATUSES:
            raise web.webapi.badrequest(
                message="Invalid status for node"
            )
        if "id" in d:
            raise web.webapi.badrequest(
                message="Manual ID setting is prohibited"
            )
        if not d:
            raise web.webapi.badrequest(
                message="No valid data received"
            )
        return d

    @classmethod
    def validate_collection_update(cls, data):
        d = cls.validate_json(data)
        if not isinstance(d, list):
            raise web.badrequest(
                "Invalid json list"
            )

        q = cls.db.query(Node)
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
        cls.db.expunge_all()
        return d


class NodeAttributesValidator(BasicValidator):
    pass


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

        q = cls.db.query(Notification)
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
        cls.db.expunge_all()
        return valid_d


class NetworkGroupValidator(BasicValidator):
    @classmethod
    def validate_collection_update(cls, data):
        d = cls.validate_json(data)
        if not isinstance(d, list):
            raise web.webapi.badrequest(
                message="It's expected to receive array, not a single object"
            )
        for i in d:
            if not 'id' in i:
                raise web.webapi.badrequest(
                    message="No 'id' param for '{0}'".format(i)
                )
        if not d:
            raise web.webapi.badrequest(
                message="No valid data received"
            )
        return d
