# -*- coding: utf-8 -*-

import re
import uuid
import string
from random import choice
from copy import deepcopy

import web
from sqlalchemy import Column, UniqueConstraint, Table
from sqlalchemy import Integer, String, Unicode, Text, Boolean
from sqlalchemy import ForeignKey, Enum
from sqlalchemy import create_engine
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

from nailgun.api.fields import JSON
from nailgun.settings import settings
from nailgun.api.validators import BasicValidator


engine = create_engine(settings.DATABASE_ENGINE)
Base = declarative_base()


class Release(Base, BasicValidator):
    __tablename__ = 'releases'
    __table_args__ = (
        UniqueConstraint('name', 'version'),
    )
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(100), nullable=False)
    version = Column(String(30), nullable=False)
    description = Column(Unicode)
    networks_metadata = Column(JSON, default=[])
    attributes_metadata = Column(JSON, default={})
    clusters = relationship("Cluster", backref="release")

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
        if web.ctx.orm.query(Release).filter(
                Release.name == d["name"]
                and Release.version == d["version"]).first():
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
        return d


class Cluster(Base, BasicValidator):
    __tablename__ = 'clusters'
    TYPES = ('compute', 'storage', 'both', 'singlenode')
    MODES = ('simple', 'ha')
    type = Column(Enum(*TYPES), nullable=False, default='both')
    mode = Column(Enum(*MODES), nullable=False, default='simple')
    redundancy = Column(Integer, nullable=True)
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(50), unique=True, nullable=False)
    release_id = Column(Integer, ForeignKey('releases.id'), nullable=False)
    nodes = relationship("Node", backref="cluster")
    tasks = relationship("Task", backref="cluster")
    attributes = relationship("Attributes", uselist=False, backref="cluster")

    @classmethod
    def validate(cls, data):
        d = cls.validate_json(data)
        if web.ctx.orm.query(Cluster).filter(
            Cluster.name == d["name"]
        ).first():
            raise web.webapi.conflict
        if d.get("release"):
            release = web.ctx.orm.query(Release).get(d.get("release"))
            if not release:
                raise web.webapi.badrequest(message="Invalid release id")
        if d.get("mode") == "ha":
            if not (isinstance(d.get("redundancy"), int) and
                    2 <= d.get("redundancy") <= 9):
                raise web.webapi.badrequest(message="Invalid redundancy")
        return d


class Node(Base, BasicValidator):
    __tablename__ = 'nodes'
    NODE_STATUSES = (
        'offline',
        'ready',
        'discover',
        'provisioning',
        'deploying',
        'error'
    )
    NODE_ROLES = (
        'controller',
        'compute',
        'storage',
    )
    NODE_ERRORS = (
        'deploy',
        'provision',
    )
    id = Column(Integer, primary_key=True)
    cluster_id = Column(Integer, ForeignKey('clusters.id'))
    name = Column(Unicode(100))
    status = Column(Enum(*NODE_STATUSES), nullable=False, default='ready')
    meta = Column(JSON)
    mac = Column(String(17), nullable=False, unique=True)
    ip = Column(String(15))
    fqdn = Column(String(255))
    manufacturer = Column(Unicode(50))
    platform_name = Column(String(150))
    os_platform = Column(String(150))
    role = Column(Enum(*NODE_ROLES))
    pending_addition = Column(Boolean, default=False)
    pending_deletion = Column(Boolean, default=False)
    error_type = Column(Enum(*NODE_ERRORS))
    error_msg = Column(String(255))

    @property
    def networks(self):
        from nailgun.network import manager as netmanager
        return netmanager.get_node_networks(self.id)

    @property
    def info(self):
        """ Safely aggregate metadata to provide short info for UI """
        result = {}

        try:
            kilobytes = int(self.meta['memory']['total'][:-2])
            gigabytes = kilobytes / 1024.0 ** 2
            result['ram'] = gigabytes
        except (KeyError, ValueError, TypeError):
            result['ram'] = None

        try:
            result['cpu'] = self.meta['cpu']['real']
            result['cores'] = self.meta['cpu']['total']
        except (KeyError, ValueError, TypeError):
            result['cpu'] = None
            result['cores'] = None

        # FIXME: disk space calculating may be wrong
        result['hdd'] = 0
        try:
            for name, info in self.meta['block_device'].iteritems():
                if re.match(r'^sd.$', name):
                    bytes = int(info['size']) * 512
                    terabytes = bytes / 1024.0 ** 4
                    result['hdd'] += terabytes
        except (AttributeError, KeyError, ValueError, TypeError):
            result['hdd'] = None

        return result

    @classmethod
    def validate(cls, data):
        d = cls.validate_json(data)
        if not "mac" in d:
            raise web.webapi.badrequest(
                message="No mac address specified"
            )
        else:
            q = web.ctx.orm.query(Node)
            if q.filter(Node.mac == d["mac"]).first():
                raise web.webapi.conflict()
        if "id" in d:
            raise web.webapi.badrequest(
                message="Manual ID setting is prohibited"
            )
        return d

    @classmethod
    def validate_update(cls, data):
        d = cls.validate_json(data)
        if "status" in d and d["status"] not in cls.NODE_STATUSES:
            raise web.webapi.badrequest(
                message="Invalid status for node"
            )
        if "id" in d:
            raise web.webapi.badrequest(
                message="Manual ID setting is prohibited"
            )
        return d

    @classmethod
    def validate_collection_update(cls, data):
        d = cls.validate_json(data)
        if not isinstance(d, list):
            raise web.badrequest(
                "Invalid json list"
            )

        q = web.ctx.orm.query(Node)
        for nd in d:
            if not "mac" in nd and not "id" in nd:
                raise web.badrequest(
                    "MAC or ID is not specified"
                )
            else:
                if "mac" in nd and not q.filter(
                    Node.mac == nd["mac"]
                ).first():
                    raise web.badrequest(
                        "Invalid MAC specified"
                    )
                if "id" in nd and not q.get(nd["id"]):
                    raise web.badrequest(
                        "Invalid ID specified"
                    )
        return d


class IPAddr(Base):
    __tablename__ = 'ip_addrs'
    id = Column(Integer, primary_key=True)
    network = Column(Integer, ForeignKey('networks.id'))
    node = Column(Integer, ForeignKey('nodes.id'))
    ip_addr = Column(String(25))


class Vlan(Base, BasicValidator):
    __tablename__ = 'vlan'
    id = Column(Integer, primary_key=True)
    network = relationship("Network")


class Network(Base, BasicValidator):
    __tablename__ = 'networks'
    id = Column(Integer, primary_key=True)
    release = Column(Integer, ForeignKey('releases.id'), nullable=False)
    name = Column(Unicode(100), nullable=False)
    access = Column(String(20), nullable=False)
    vlan_id = Column(Integer, ForeignKey('vlan.id'))
    cluster_id = Column(Integer, ForeignKey('clusters.id'))
    cidr = Column(String(25), nullable=False)
    gateway = Column(String(25))
    nodes = relationship(
        "Node",
        secondary=IPAddr.__table__,
        backref="networks")

    @classmethod
    def validate_collection_update(cls, data):
        d = cls.validate_json(data)
        if not isinstance(d, list):
            raise web.webapi.badrequest(
                message="It's expected to receive array, not single object"
            )
        for i in d:
            if not 'id' in i:
                raise web.webapi.badrequest(
                    message="No 'id' param for '%'" % i
                )
        return d


class Attributes(Base, BasicValidator):
    __tablename__ = 'attributes'
    id = Column(Integer, primary_key=True)
    cluster_id = Column(Integer, ForeignKey('clusters.id'))
    editable = Column(JSON)
    generated = Column(JSON)

    def generate_fields(self):
        def traverse(cdict):
            new_dict = {}
            if cdict:
                for i, val in cdict.iteritems():
                    if isinstance(val, str) or isinstance(val, unicode):
                        if val in ["", u""]:
                            new_dict[i] = self._generate_pwd()
                        else:
                            new_dict[i] = val
                    elif isinstance(val, dict):
                        new_dict[i] = traverse(val)
            return new_dict
        self.generated = traverse(self.generated)

        web.ctx.orm.add(self)
        web.ctx.orm.commit()

    def _generate_pwd(self, length=8):
        chars = string.letters + string.digits
        return u''.join([choice(chars) for _ in xrange(length)])

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

    def merged_attrs(self):
        return self._dict_merge(self.generated, self.editable)

    def _dict_merge(self, a, b):
        '''recursively merges dict's. not just simple a['key'] = b['key'], if
        both a and bhave a key who's value is a dict then dict_merge is called
        on both values and the result stored in the returned dictionary.'''
        if not isinstance(b, dict):
            return b
        result = deepcopy(a)
        for k, v in b.iteritems():
            if k in result and isinstance(result[k], dict):
                    result[k] = self._dict_merge(result[k], v)
            else:
                result[k] = deepcopy(v)
        return result


class Task(Base, BasicValidator):
    __tablename__ = 'tasks'
    TASK_STATUSES = (
        'ready',
        'running',
        'error'
    )
    TASK_TYPES = (
        'super',
        'deploy',
        'deployment',
        'deletion',
        'verify_networks'
    )
    id = Column(Integer, primary_key=True)
    cluster_id = Column(Integer, ForeignKey('clusters.id'))
    uuid = Column(String(36), nullable=False,
                  default=lambda: str(uuid.uuid4()))
    name = Column(Enum(*TASK_TYPES), nullable=False, default='super')
    error = Column(Text)
    status = Column(Enum(*TASK_STATUSES), nullable=False, default='running')
    progress = Column(Integer)
    parent_id = Column(Integer, ForeignKey('tasks.id'))
    subtasks = relationship(
        "Task",
        backref=backref('parent', remote_side=[id])
    )

    def execute(self, instance):
        return instance.execute(self)

    def create_subtask(self, name):
        if not name:
            raise ValueError("Subtask name not specified")

        task = Task(
            name=name,
            cluster=self.cluster
        )
        self.subtasks.append(task)
        web.ctx.orm.commit()
        return task
