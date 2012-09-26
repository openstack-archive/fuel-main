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
    def deploy_resp(cls, nodes):
        logging.info("Received deploy_resp")
        updated = []
        for nd_id, fields in nodes.iteritems():
            node = cls.db.query(Node).get(int(nd_id))
            for field, value in fields.iteritems():
                setattr(node, field, value)
            cls.db.add(node)
            updated.append(node.id)
        cls.db.commit()
        return updated


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
