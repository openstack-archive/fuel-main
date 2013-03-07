# -*- coding: utf-8 -*-

import logging
import threading

from kombu import Connection, Exchange, Queue

import nailgun.rpc as rpc
from nailgun.logger import logger
from nailgun.rpc.receiver import NailgunReceiver


class RPCThread(threading.Thread):
    def __init__(self, rec_class=NailgunReceiver):
        super(RPCThread, self).__init__()
        self.receiver = rec_class()
        self.conn = rpc.create_connection(True)
        self.conn.create_consumer('nailgun', self.receiver)

    def run(self):
        logger.info("Starting RPC thread...")
        self.running = True
        # TODO: implement fail-safe auto-reloading
        self.conn.consume()
        self.conn.close()
