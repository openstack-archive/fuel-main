# -*- coding: utf-8 -*-

import time
import Queue
import logging
import threading

from sqlalchemy.orm import scoped_session, sessionmaker

import rpc
from db import Query
from api.models import engine

rpc_queue = Queue.Queue()


class TestReceiver(object):
    """Simple Proxy class so the consumer has methods to call.

    Uses static methods because we aren't actually storing any state.

    """

    @staticmethod
    def echo(value):
        """Simply returns whatever value is sent in."""
        return value

    @staticmethod
    def multicall_three_nones(value):
        yield None
        yield None
        yield None

    @staticmethod
    def echo_three_times_yield(value):
        yield value
        yield value + 1
        yield value + 2

    @staticmethod
    def fail(value):
        """Raises an exception with the value sent in."""
        raise Exception(value)

    @staticmethod
    def block(value):
        time.sleep(2)


import eventlet
eventlet.monkey_patch()


class RPCThread(threading.Thread):
    def __init__(self, testmode=False):
        super(RPCThread, self).__init__()
        self.queue = rpc_queue
        self.db = scoped_session(
            sessionmaker(bind=engine, query_cls=Query)
        )
        self.conn = rpc.create_connection(True)
        self.testmode = testmode
        if not self.testmode:
            self.receiver = TestReceiver()
            self.conn.create_consumer('test', self.receiver, False)
            self.conn.consume_in_thread()

    def run(self):
        logging.info("Starting RPC thread...")
        self.running = True

        while self.running:
            try:
                msg = self.queue.get_nowait()
                getattr(self, msg)()
                if not self.running:
                    break
            except Queue.Empty:
                pass
            try:
                ans = rpc.call('test', {
                    "method": "echo",
                    "args": {
                        "value": 1
                    }
                })
                # update db here with data
            except Exception as error:
                # update db here with error
                logging.info("ERROR!!!!")
            time.sleep(5)
        self.conn.close()

    def exit(self):
        logging.info("Stopping RPC thread...")
        self.running = False
