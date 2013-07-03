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
import traceback
import threading

from kombu import Connection, Exchange, Queue
from kombu.mixins import ConsumerMixin

import nailgun.rpc as rpc
from nailgun.settings import settings
from nailgun.logger import logger
from nailgun.rpc.receiver import NailgunReceiver
from nailgun.db import db


class RPCConsumer(ConsumerMixin):

    def __init__(self, connection, receiver):
        self.connection = connection
        self.receiver = receiver

    def get_consumers(self, Consumer, channel):
        return [Consumer(queues=[rpc.nailgun_queue],
                         callbacks=[self.consume_msg])]

    def consume_msg(self, body, msg):
        callback = getattr(self.receiver, body["method"])
        try:
            callback(**body["args"])
        except Exception as exc:
            logger.error(traceback.format_exc())
            db().rollback()
        finally:
            db().commit()
            db().expire_all()
        msg.ack()


class RPCKombuThread(threading.Thread):

    def __init__(self, rcvr_class=NailgunReceiver):
        super(RPCKombuThread, self).__init__()
        self.stoprequest = threading.Event()
        self.receiver = rcvr_class
        self.connection = None

    def join(self, timeout=None):
        self.stoprequest.set()
        # this should interrupt inner kombu event loop
        # actually, it doesn't
        self.consumer.should_stop = True
        super(RPCKombuThread, self).join(timeout)

    def run(self):
        with Connection(rpc.conn_str) as conn:
            self.consumer = RPCConsumer(conn, self.receiver)
            self.consumer.run()
