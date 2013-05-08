# -*- coding: utf-8 -*-

from kombu import Connection, Exchange, Queue

from nailgun.settings import settings
from nailgun.logger import logger

creds = (
    ("userid", "guest"),
    ("password", "guest"),
    ("hostname", "localhost"),
    ("port", "5672"),
)

conn_str = 'amqp://{0}:{1}@{2}:{3}//'.format(
    *[settings.RABBITMQ.get(*cred) for cred in creds]
)

naily_exchange = Exchange(
    'naily',
    'topic',
    durable=True
)

naily_queue = Queue(
    'naily',
    exchange=naily_exchange,
    routing_key='naily'
)

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


def cast(name, message):
    with Connection(conn_str) as conn:
        with conn.Producer(serializer='json') as producer:
            producer.publish(message,
                             exchange=naily_exchange, routing_key=name,
                             declare=[naily_queue])
