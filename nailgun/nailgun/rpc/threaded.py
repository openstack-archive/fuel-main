# -*- coding: utf-8 -*-

import time
import Queue
import logging
import threading

import greenlet
import eventlet
from sqlalchemy.orm import scoped_session, sessionmaker

import nailgun.rpc as rpc
from nailgun.db import Query
from nailgun.api.models import engine, Node, Task

rpc_queue = Queue.Queue()


class TaskNotFound(Exception):
    pass


class NailgunReceiver(object):
    db = scoped_session(
        sessionmaker(bind=engine, query_cls=Query)
    )

    @classmethod
    def __update_task_status(cls, uuid, status, error=""):
        task = cls.db.query(Task).filter_by(uuid=uuid).first()
        if not task:
            logging.error("Can't set status='%s', error='%s':no task \
                    with UUID %s found!", status, error, uuid)
        task.status = status
        if error:
            task.error = error
        cls.db.add(task)
        cls.db.commit()

    @classmethod
    def deploy_resp(cls, **kwargs):
        logging.info("RPC method deploy_resp received: %s" % kwargs)
        task_uuid = kwargs.get('task_uuid')
        nodes = kwargs.get('nodes') or []
        error_msg = kwargs.get('error')
        status = kwargs.get('status')

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

        if status:
            cls.__update_task_status(task_uuid, status, error_msg)

    @classmethod
    def verify_networks_resp(cls, **kwargs):
        logging.info("RPC method verify_networks_resp received: %s" % kwargs)
        task_uuid = kwargs.get('task_uuid')
        nodes = kwagrs.get('nodes') or []
        error_msg = kwargs.get('error')
        status = kwargs.get('status')
        # TODO complete this


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
        logging.info("Starting RPC thread...")
        self.running = True
        # TODO: implement fail-safe auto-reloading
        self.conn.consume()
        self.conn.close()
