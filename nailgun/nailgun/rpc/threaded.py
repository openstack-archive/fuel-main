# -*- coding: utf-8 -*-

import Queue
import logging
import threading

import nailgun.rpc as rpc
from nailgun.rpc.receiver import NailgunReceiver

logger = logging.getLogger(__name__)

rpc_queue = Queue.Queue()


class RPCThread(threading.Thread):
    def __init__(self, rec_class=NailgunReceiver):
        super(RPCThread, self).__init__()
        self.queue = rpc_queue
        self.receiver = rec_class()
        self.conn = rpc.create_connection(True)
        self.conn.create_consumer('nailgun', self.receiver)

    def run(self):
        logger.info("Starting RPC thread...")
        self.running = True
        # TODO: implement fail-safe auto-reloading
        self.conn.consume()
        self.conn.close()
