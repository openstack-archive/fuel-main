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

import json

from kombu import Connection
from kombu import Exchange
from kombu import Queue

from nailgun.logger import logger
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
    logger.debug(
        "RPC cast to orchestrator:\n{0}".format(
            json.dumps(message, indent=4)
        )
    )
    with Connection(conn_str) as conn:
        with conn.Producer(serializer='json') as producer:
            producer.publish(message,
                             exchange=naily_exchange, routing_key=name,
                             declare=[naily_queue])
