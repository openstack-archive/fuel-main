# -*- coding: utf-8 -*-

import json

import web
import ipaddr
from sqlalchemy import Column, UniqueConstraint, Table
from sqlalchemy import Integer, String, Unicode, Boolean, ForeignKey, Enum
from sqlalchemy import create_engine
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

import settings
from api.fields import JSON
from api.validators import BasicValidator

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
    networks_metadata = Column(JSON)
    roles = relationship("Role", backref="release")
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
                Release.name == d["name"] \
                    and Release.version == d["version"]
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
        return d


class Role(Base, BasicValidator):
    __tablename__ = 'roles'
    __table_args__ = (
        UniqueConstraint('name', 'release_id'),
    )
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(100), nullable=False)
    release_id = Column(Integer, ForeignKey('releases.id'), nullable=False)


class Cluster(Base, BasicValidator):
    __tablename__ = 'clusters'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(100), unique=True, nullable=False)
    release_id = Column(Integer, ForeignKey('releases.id'), nullable=False)
    nodes = relationship("Node", backref="cluster")

    @classmethod
    def validate(cls, data):
        d = cls.validate_json(data)
        if web.ctx.orm.query(Cluster).filter(
            Cluster.name == d["name"]
        ).first():
            raise web.webapi.conflict
        if d["release"]:
            release = web.ctx.orm.query(Release).get(d["release"])
            if not release:
                raise web.webapi.badrequest(message="Invalid release id")
        return d


nodes_roles = Table('nodes_roles', Base.metadata,
    Column('node', Integer, ForeignKey('nodes.id')),
    Column('role', Integer, ForeignKey('roles.id'))
)

nodes_new_roles = Table('nodes_new_roles', Base.metadata,
    Column('node', Integer, ForeignKey('nodes.id')),
    Column('role', Integer, ForeignKey('roles.id'))
)


class Node(Base, BasicValidator):
    __tablename__ = 'nodes'
    NODE_STATUSES = (
        'offline',
        'ready',
        'discover',
        'deploying',
        'error'
    )
    id = Column(Integer, primary_key=True)
    cluster_id = Column(Integer, ForeignKey('clusters.id'))
    name = Column(Unicode(100))
    status = Column(Enum(*NODE_STATUSES), nullable=False, default='ready')
    meta = Column(JSON)
    mac = Column(String(17), nullable=False)
    ip = Column(String(15))
    fqdn = Column(String(255))
    manufacturer = Column(Unicode(50))
    platform_name = Column(String(150))
    os_platform = Column(String(150))
    roles = relationship("Role",
                secondary=nodes_roles,
                backref="nodes")
    new_roles = relationship("Role",
                secondary=nodes_new_roles)
    redeployment_needed = Column(Boolean, default=False)

    @property
    def info(self):
        """ Safely aggregate metadata to provide short info for UI """
        result = {}

        try:
            kilobytes = int(self.meta['memory']['total'][:-2])
            gigabytes = kilobytes / 1024.0 ** 2
            result['ram'] = gigabytes
        except Exception:
            result['ram'] = None

        try:
            result['cpu'] = self.meta['cpu']['real']
            result['cores'] = self.meta['cpu']['total']
        except Exception:
            result['cpu'] = None
            result['cores'] = None

        # FIXME: disk space calculating may be wrong
        try:
            result['hdd'] = 0
            for name, info in self.meta['block_device'].iteritems():
                if re.match(r'^sd.$', name):
                    bytes = int(info['size']) * 512
                    terabytes = bytes / 1024.0 ** 4
                    result['hdd'] += terabytes
        except Exception:
            result['hdd'] = None

        return result

    @classmethod
    def validate(cls, data):
        d = cls.validate_json(data)
        if not "mac" in d:
            raise web.webapi.badrequest(message="No mac address specified")
        return d

    @classmethod
    def validate_update(cls, data):
        d = cls.validate_json(data)
        if "status" in d and d["status"] not in cls.NODE_STATUSES:
            raise web.webapi.badrequest(message="Invalid status for node")
        return d


class IPAddr(Base):
    __tablename__ = 'ip_addrs'
    id = Column(Integer, primary_key=True)
    network = Column(Integer, ForeignKey('networks.id'))
    node = Column(Integer, ForeignKey('nodes.id'))
    ip_addr = Column(String(25))


class Network(Base, BasicValidator):
    __tablename__ = 'networks'
    id = Column(Integer, primary_key=True)
    release = Column(Integer, ForeignKey('releases.id'), nullable=False)
    name = Column(Unicode(20), nullable=False)
    access = Column(String(20), nullable=False)
    vlan_id = Column(Integer)
    network = Column(String(25), nullable=False)
    range_l = Column(String(25))
    range_h = Column(String(25))
    gateway = Column(String(25))
    nodes = relationship("Node",
                secondary=IPAddr.__table__,
                backref="networks")

    @property
    def netmask(self):
        return str(ipaddr.IPv4Network(self.network).netmask)

    @property
    def broadcast(self):
        return str(ipaddr.IPv4Network(self.network).broadcast)
