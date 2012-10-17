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
        task = cls.db.query(Task).filter(Task.uuid == uuid).first()
        if not task:
            raise TaskNotFound()
        task.status = status
        if error:
            task.error = error
        cls.db.add(task)
        cls.db.commit()

    @classmethod
    def deploy_resp(cls, task_uuid, nodes):
        logging.info("Received deploy_resp")
        updated = []

        error_nodes = []
        for nd_id, fields in nodes.iteritems():
            node = cls.db.query(Node).get(int(nd_id))
            for field, value in fields.iteritems():
                # TODO: add logic according to API
                if field == "status":
                    setattr(node, field, value)
                    if value == "error":
                        error_nodes.append(node)
            cls.db.add(node)
            updated.append(node.id)
        cls.db.commit()

        try:
            if error_nodes:
                nodes_info = [
                    unicode({
                        "MAC": n.mac,
                        "IP": n.ip or "Unknown",
                        "NAME": n.name or "Unknown"
                    }) for n in error_nodes
                ]
                cls.__update_task_status(
                    task_uuid,
                    "error",
                    "Failed to deploy nodes:\n%s" % "\n".join(nodes_info)
                )
            else:
                cls.__update_task_status(task_uuid, "ready")
        except TaskNotFound:
            logging.error("No task with UUID %s found!" % uuid)
        return updated

    @classmethod
    def verify_networks_resp(cls, task_uuid, result):
        pass


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
