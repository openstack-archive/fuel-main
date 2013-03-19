# -*- coding: utf-8 -*-

import time
import traceback
import threading

from kombu import Connection, Exchange, Queue
from kombu.mixins import ConsumerMixin

import nailgun.rpc as rpc
from nailgun.settings import settings
from nailgun.db import NoCacheQuery, engine
from nailgun.logger import logger
from nailgun.rpc.receiver import NailgunReceiver


class RPCConsumer(ConsumerMixin):

    def __init__(self, connection, receiver):
        self.connection = connection
        self.receiver = receiver
        self.receiver.initialize()

    def get_consumers(self, Consumer, channel):
        return [Consumer(queues=[rpc.nailgun_queue],
                         callbacks=[self.consume_msg])]

    def consume_msg(self, body, msg):
        callback = getattr(self.receiver, body["method"])
        try:
            callback(**body["args"])
        except Exception as exc:
            logger.error(traceback.format_exc())
            self.receiver.db.rollback()
        finally:
            self.receiver.db.commit()
            self.receiver.db.expire_all()
        msg.ack()


class RPCKombuThread(threading.Thread):

    def __init__(self, rcvr_class=NailgunReceiver):
        super(RPCKombuThread, self).__init__()
        self.stoprequest = threading.Event()
        self.receiver = rcvr_class
        self.connection = None

    def join(self, timeout=None):
        self.stoprequest.set()
        super(RPCKombuThread, self).join(timeout)

    def run(self):
        with Connection(rpc.conn_str) as conn:
            try:
                RPCConsumer(conn, self.receiver).run()
            except KeyboardInterrupt:
                return
