# -*- coding: utf-8 -*-

import time
import threading
import traceback
from datetime import datetime
from itertools import repeat
from sqlalchemy.sql import not_

from nailgun.notifier import notifier
from nailgun.db import make_session
from nailgun.settings import settings
from nailgun.api.models import Node
from nailgun.logger import logger


class KeepAliveThread(threading.Thread):

    def __init__(self, interval=None, timeout=None):
        super(KeepAliveThread, self).__init__()
        self.stop_status_checking = threading.Event()
        self.interval = interval or settings.KEEPALIVE['interval']
        self.timeout = timeout or settings.KEEPALIVE['timeout']
        self.db = make_session()

    def reset_nodes_timestamp(self):
        self.db.query(Node).update({'timestamp': datetime.now()})
        self.db.commit()

    def join(self, timeout=None):
        self.stop_status_checking.set()
        super(KeepAliveThread, self).join(timeout)

    def sleep(self, interval=None):
        map(
            lambda i: not self.stop_status_checking.isSet() and time.sleep(i),
            repeat(1, interval or self.interval)
        )

    def run(self):
        while True:
            try:
                self.reset_nodes_timestamp()

                while not self.stop_status_checking.isSet():
                    self.update_status_nodes()
                    self.sleep()
            except Exception as exc:
                err = str(exc)
                logger.error(traceback.format_exc())
                time.sleep(1)

            if self.stop_status_checking.isSet():
                break

    def update_status_nodes(self):
        for node_db in self.db.query(Node).filter(
            # nodes may become unresponsive while provisioning
            not_(Node.status == 'provisioning')):
            timedelta = (datetime.now() - node_db.timestamp).seconds
            if timedelta > self.timeout:
                logger.warning(
                    u"Node '{0}' seems to be offline "
                    "for {1} seconds...".format(
                        node_db.name,
                        timedelta))
                if node_db.online:
                    node_db.online = False
                    self.db.commit()
                    notifier.notify(
                        "error",
                        u"Node '{0}' has gone away".format(
                            node_db.human_readable_name),
                        node_id=node_db.id)
