# -*- coding: utf-8 -*-

from kombu import Connection, Exchange, Queue

from nailgun.settings import settings

creds = (
    ("userid", "guest"),
    ("password", "guest"),
    ("hostname", "localhost"),
    ("port", "5672"),
)

conn_str = 'amqp://{0}:{1}@{2}:{3}//'.format(
    *[settings.RABBITMQ.get(*cred) for cred in creds]
)


def cast(name, message):
    nailgun_exchange = Exchange(
        'naily',
        'topic',
        durable=True
    )
    nailgun_queue = Queue(
        'naily',
        exchange=nailgun_exchange,
        routing_key='naily'
    )
    with Connection(conn_str) as conn:
        with conn.Producer(serializer='json') as producer:
            producer.publish(message,
                             exchange=nailgun_exchange, routing_key='naily',
                             declare=[nailgun_queue])
