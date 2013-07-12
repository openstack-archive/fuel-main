# -*- coding: utf-8 -*-

#    Copyright 2013 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import time
import threading
import traceback
from datetime import datetime, timedelta
from itertools import repeat
from sqlalchemy.sql import not_
from sqlalchemy import extract

from nailgun import notifier
from nailgun.db import db
from nailgun.settings import settings
from nailgun.api.models import Node
from nailgun.logger import logger


class KeepAliveThread(threading.Thread):

    def __init__(self, interval=None, timeout=None):
        super(KeepAliveThread, self).__init__()
        self.stop_status_checking = threading.Event()
        self.interval = interval or settings.KEEPALIVE['interval']
        self.timeout = timeout or settings.KEEPALIVE['timeout']

    def reset_nodes_timestamp(self):
        db().query(Node).update({'timestamp': datetime.now()})
        db().commit()

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
        to_update = db().query(Node).filter(
            not_(Node.status == 'provisioning')
        ).filter(
            datetime.now() > (Node.timestamp + timedelta(seconds=self.timeout))
        ).filter_by(
            online=True
        )
        for node_db in to_update.all():
            notifier.notify(
                "error",
                u"Node '{0}' has gone away".format(
                    node_db.human_readable_name),
                node_id=node_db.id
            )
        to_update.update({"online": False})
        db().commit()
