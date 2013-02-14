# -*- coding: utf-8 -*-

import time
import logging
import threading
from itertools import repeat

# from nailgun.db import orm
# from nailgun.logger import logger


class KeepAliveThread(threading.Thread):
    nodes = []

    @classmethod
    def register(cls, node):
        cls.nodes.append(node)

    def __init__(self, timeout=6):
        super(KeepAliveThread, self).__init__()
        self.stoprequest = threading.Event()
        self.timeout = timeout

    def join(self, timeout=None):
        self.stoprequest.set()
        super(KeepAliveThread, self).join(timeout)

    def run(self):
        # logger.info("Starting KeepAlive thread...")
        while not self.stoprequest.isSet():
            for node in self.nodes:
                print node
            map(
                lambda i: not self.stoprequest.isSet() and time.sleep(i),
                repeat(1, self.timeout)
            )


if __name__ == "__main__":
    t = KeepAliveThread()
    t.start()
    time.sleep(3)
    t.register("OLOLO")
    time.sleep(10)
    t.join()
