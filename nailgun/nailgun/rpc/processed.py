# -*- coding: utf-8 -*-

import logging
from multiprocessing import Process

from kombu import Connection, Exchange, Queue

import nailgun.rpc as rpc
from nailgun.settings import settings
from nailgun.db import NoCacheQuery, engine
from nailgun.logger import logger
from nailgun.rpc.receiver import NailgunReceiver


class RPCKombuProcess(Process):

    def consume(self, body, msg):
        callback = getattr(self.receiver, body["method"])
        try:
            callback(**body["args"])
        except Exception as exc:
            self.receiver.db.rollback()
        finally:
            self.receiver.db.commit()
            self.receiver.db.expunge_all()
        msg.ack()

    def receive(self, rec_class):
        self.receiver = rec_class
        self.receiver.initialize()
        nailgun_exchange = Exchange(
            'nailgun',
            'topic',
            durable=True
        )
        nailgun_queue = Queue(
            'nailgun',
            exchange=nailgun_exchange,
            routing_key='nailgun'
        )

        with Connection(rpc.conn_str) as conn:
            with conn.Consumer(
                nailgun_queue,
                callbacks=[self.consume]
            ) as consumer:
                while True:
                    conn.drain_events()

    def __init__(self, queue_name='nailgun', rec_class=NailgunReceiver):
        super(RPCKombuProcess, self).__init__(
            target=self.receive,
            args=(
                rec_class,
            )
        )
