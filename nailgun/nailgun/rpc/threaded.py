# -*- coding: utf-8 -*-

import time
import Queue
import logging

logger = logging.getLogger(__name__)

import threading
import itertools

import greenlet
import eventlet
from sqlalchemy.orm import scoped_session, sessionmaker

import nailgun.rpc as rpc
from nailgun.db import Query
from nailgun.api.models import engine, Node, Task, Network

rpc_queue = Queue.Queue()


class TaskNotFound(Exception):
    pass


class NailgunReceiver(object):
    db = scoped_session(
        sessionmaker(bind=engine, query_cls=Query)
    )

    @classmethod
    def __update_task_status(cls, uuid, status, progress, error=""):
        task = cls.db.query(Task).filter_by(uuid=uuid).first()
        if not task:
            logger.error("Can't set status='%s', error='%s':no task \
                    with UUID %s found!", status, error, uuid)
            return
        data = {'status': status, 'progress': progress, 'error': error}
        for key, value in data.iteritems():
            if value:
                setattr(task, key, value)
        cls.db.add(task)
        cls.db.commit()

    @classmethod
    def remove_nodes_resp(cls, **kwargs):
        logger.info("RPC method remove_nodes_resp received: %s" % kwargs)
        task_uuid = kwargs.get('task_uuid')
        nodes = kwargs.get('nodes') or []
        nodes = kwargs.get('error_nodes') or []
        error_msg = kwargs.get('error')
        status = kwargs.get('status')

    @classmethod
    def deploy_resp(cls, **kwargs):
        logger.info("RPC method deploy_resp received: %s" % kwargs)
        task_uuid = kwargs.get('task_uuid')
        nodes = kwargs.get('nodes') or []
        error_msg = kwargs.get('error')
        status = kwargs.get('status')
        progress = kwargs.get('progress')

        error_nodes = []
        for node in nodes:
            # TODO if not found? or node['uid'] not specified?
            node_db = cls.db.query(Node).filter_by(fqdn=node['uid']).first()
            if node.get('status'):
                node_db.status = node['status']
                cls.db.add(node_db)
                cls.db.commit()
                if node['status'] == 'error':
                    error_nodes.append(node_db)

        if error_nodes:
            nodes_info = [
                unicode({
                    "MAC": n.mac,
                    "IP": n.ip or "Unknown",
                    "NAME": n.name or "Unknown"
                }) for n in error_nodes
            ]
            error_msg = "Failed to deploy nodes:\n%s" % "\n".join(nodes_info)
            status = 'error'

        cls.__update_task_status(task_uuid, status, progress, error_msg)

    @classmethod
    def verify_networks_resp(cls, **kwargs):
        logger.info("RPC method verify_networks_resp received: %s" % kwargs)
        task_uuid = kwargs.get('task_uuid')
        networks = kwargs.get('networks') or []
        error_msg = kwargs.get('error')
        status = kwargs.get('status')
        progress = kwargs.get('progress')

        # We simply check that each node received all vlans for cluster
        task = cls.db.query(Task).filter_by(uuid=task_uuid).first()
        if not task:
            logger.error("verify_networks_resp: task \
                    with UUID %s found!", task_uuid)
            return
        nets_db = cls.db.query(Network).filter_by(cluster_id=
                                                  task.cluster_id).all()
        vlans_db = [net.vlan_id for net in nets_db]
        error_nodes = []
        for x in networks:
            # Now - for all interfaces (eth0, eth1, etc.)
            for iface in x['networks']:
                absent_vlans = list(set(vlans_db) - set(iface['vlans']))
                if absent_vlans:
                    error_nodes.append({'uid': x['uid'],
                                        'absent_vlans': absent_vlans})

        if error_nodes:
            error_msg = "Following nodes do not have vlans:\n%s" % error_nodes
            logger.error(error_msg)
            status = 'error'

        cls.__update_task_status(task_uuid, status, progress, error_msg)


class RPCThread(threading.Thread):
    def __init__(self):
        super(RPCThread, self).__init__()
        self.queue = rpc_queue
        self.db = scoped_session(
            sessionmaker(bind=engine, query_cls=Query)
        )
        self.receiver = NailgunReceiver()
        self.conn = rpc.create_connection(True)
        self.conn.create_consumer('nailgun', self.receiver)

    def run(self):
        logger.info("Starting RPC thread...")
        self.running = True
        # TODO: implement fail-safe auto-reloading
        self.conn.consume()
        self.conn.close()
