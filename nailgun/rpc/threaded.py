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


class RPCThread(threading.Thread):
    def __init__(self):
        super(RPCThread, self).__init__()
        self.queue = rpc_queue
        self.db = scoped_session(
            sessionmaker(bind=engine, query_cls=Query)
        )
        self.conn = rpc.create_connection(True)

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
                pass
                # TODO: implement real rpc.call()
                # ans = rpc.call('test', {
                #     "method": "echo",
                #     "args": {
                #         "value": 1
                #     }
                # })
                # update db here with data
            except Exception as error:
                # update db here with error
                logging.info("ERROR!!!!")
            time.sleep(5)
        self.conn.close()

    def exit(self):
        logging.info("Stopping RPC thread...")
        self.running = False
