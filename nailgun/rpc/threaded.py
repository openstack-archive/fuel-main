# -*- coding: utf-8 -*-

import time
import Queue
import logging
import threading

import greenlet
import eventlet
from sqlalchemy.orm import scoped_session, sessionmaker

import rpc
from db import Query
from api.models import engine, Node

rpc_queue = Queue.Queue()


class NailgunReceiver(object):
    db = scoped_session(
        sessionmaker(bind=engine, query_cls=Query)
    )

    @classmethod
    def node_error(cls, node_id):
        logging.info("Setting node %d status to 'error'", node_id)
        node = cls.db.query(Node).get(node_id)
        node.status = 'error'
        cls.db.add(node)
        cls.db.commit()


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
