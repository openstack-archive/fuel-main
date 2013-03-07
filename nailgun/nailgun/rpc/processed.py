# -*- coding: utf-8 -*-

import logging
from multiprocessing import Process

import eventlet
from kombu import Connection, Exchange, Queue
from sqlalchemy.orm import scoped_session, sessionmaker

if __name__ == "__main__":
    import os
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import nailgun.rpc as rpc
from nailgun.settings import settings
from nailgun.db import NoCacheQuery, engine
from nailgun.logger import logger
from nailgun.rpc.receiver import NailgunReceiver


class RPCProcess(Process):

    def create_receiver(self, queue_name, rec_class):
        eventlet.monkey_patch()
        self.receiver = rec_class()
        self.conn = rpc.create_connection(True)
        self.conn.create_consumer(queue_name, self.receiver)
        self.conn.consume()
        self.conn.close()

    def __init__(self, queue_name='nailgun', rec_class=NailgunReceiver):
        super(RPCProcess, self).__init__(
            target=self.create_receiver,
            args=(
                queue_name,
                rec_class
            )
        )


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

        creds = (
            ("userid", "guest"),
            ("password", "guest"),
            ("hostname", "localhost"),
            ("port", "5672"),
        )

        conn_str = 'amqp://{0}:{1}@{2}:{3}//'.format(
            *[settings.RABBITMQ.get(*cred) for cred in creds]
        )
        print conn_str

        with Connection(conn_str) as conn:
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


if __name__ == "__main__":
    rpc_process = RPCKombuProcess()
    rpc_process.start()
