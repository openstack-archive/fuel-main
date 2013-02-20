# -*- coding: utf-8 -*-

import time
import logging
import threading
from datetime import datetime
from itertools import repeat

from sqlalchemy.sql import not_

from nailgun.db import orm
from nailgun.settings import settings
from nailgun.api.models import Node
from nailgun.logger import logger


class KeepAliveThread(threading.Thread):

    def __init__(self, interval=None, timeout=None):
        super(KeepAliveThread, self).__init__()
        self.stoprequest = threading.Event()
        self.interval = interval or settings.KEEPALIVE['interval']
        self.timeout = timeout or settings.KEEPALIVE['timeout']
        self.db = orm()

    def join(self, timeout=None):
        self.stoprequest.set()
        super(KeepAliveThread, self).join(timeout)

    def sleep(self, interval=None):
        map(
            lambda i: not self.stoprequest.isSet() and time.sleep(i),
            repeat(1, interval or self.interval)
        )

    def run(self):
        while not self.stoprequest.isSet():
            for node_db in self.db.query(Node).filter(
                # nodes may become unresponsive while provisioning
                not_(Node.status == 'provisioning')
            ):
                now = datetime.now()
                if (now - node_db.timestamp).seconds > self.timeout:
                    logger.warning(
                        "Node '{0}' seems to be offline "
                        "for {1} seconds...".format(
                            node_db.name,
                            (now - node_db.timestamp).seconds
                        )
                    )
                    if node_db.status != 'offline':
                        node_db.status = 'offline'
                        self.db.add(node_db)
                        self.db.commit()
            self.sleep()
