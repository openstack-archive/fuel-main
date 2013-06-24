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


import web
import time
import logging
import threading
from itertools import repeat
from random import randrange, shuffle

from kombu import Connection, Exchange, Queue
from sqlalchemy.orm import object_mapper, ColumnProperty

from nailgun.db import make_session
from nailgun.settings import settings
from nailgun.logger import logger
from nailgun.errors import errors
from nailgun.notifier import notifier
from nailgun.api.models import Network, Node, NodeAttributes
from nailgun.network.manager import NetworkManager
from nailgun.rpc.receiver import NailgunReceiver


class FakeThread(threading.Thread):
    def __init__(self, data=None, params=None, group=None, target=None,
                 name=None, verbose=None, join_to=None):
        threading.Thread.__init__(self, group=group, target=target, name=name,
                                  verbose=verbose)
        self.data = data
        self.params = params
        self.join_to = join_to
        self.tick_count = int(settings.FAKE_TASKS_TICK_COUNT) or 20
        self.low_tick_count = self.tick_count - 10
        if self.low_tick_count < 0:
            self.low_tick_count = 0
        self.tick_interval = int(settings.FAKE_TASKS_TICK_INTERVAL) or 3

        self.task_uuid = data['args'].get(
            'task_uuid'
        )
        self.respond_to = data['respond_to']
        self.stoprequest = threading.Event()

    def run(self):
        if self.join_to:
            self.join_to.join()

    def rude_join(self, timeout=None):
        self.stoprequest.set()
        super(FakeThread, self).join(timeout)

    def sleep(self, timeout):
        map(
            lambda i: not self.stoprequest.isSet() and time.sleep(i),
            repeat(1, timeout)
        )


class FakeDeploymentThread(FakeThread):
    def message_gen(self):
        # TEST: we can fail at any stage:
        # "provisioning" or "deployment"
        error = self.params.get("error")
        # TEST: error message from "orchestrator"
        error_msg = self.params.get("error_msg", "")
        # TEST: we can set node offline at any stage:
        # "provisioning" or "deployment"
        offline = self.params.get("offline")
        # TEST: we can set task to ready no matter what
        # True or False
        task_ready = self.params.get("task_ready")

        kwargs = {
            'task_uuid': self.task_uuid,
            'nodes': self.data['args']['nodes'],
            'status': 'running'
        }

        next_st = {
            "discover": "provisioning",
            "provisioning": "provisioned",
            "provisioned": "deploying",
            "deploying": "ready"
        }

        ready = False
        while not ready and not self.stoprequest.isSet():
            for n in kwargs['nodes']:
                if n['status'] == 'error' or not n['online']:
                    n['progress'] = 100
                    n['error_type'] = 'provision'
                    continue
                elif n['status'] == 'discover':
                    n['status'] = next_st[n['status']]
                    n['progress'] = 0
                elif n['status'] != 'provisioned':
                    n['progress'] += randrange(
                        self.low_tick_count,
                        self.tick_count
                    )
                    if n['progress'] >= 100:
                        n['progress'] = 100
                        n['status'] = next_st[n['status']]
            if error == "provisioning":
                shuffle(kwargs['nodes'])
                kwargs['nodes'][0]['status'] = "error"
                kwargs['nodes'][0]['error_type'] = "provision"
                kwargs['error'] = error_msg
                error = None
            yield kwargs
            if all(map(
                lambda n: n['status'] in (
                    'provisioned',
                    'error'
                ) or not n['online'],
                kwargs['nodes']
            )):
                ready = True
            else:
                self.sleep(self.tick_interval)

        error_nodes = filter(
            lambda n: n['status'] == 'error',
            kwargs['nodes']
        )
        offline_nodes = filter(
            lambda n: n['online'] is False,
            kwargs['nodes']
        )
        if error_nodes or offline_nodes:
            kwargs['status'] = 'error'
            # TEST: set task to ready no matter what
            if task_ready:
                kwargs['status'] = 'ready'
            kwargs['progress'] = 100
            yield kwargs
            return

        ready = False
        while not ready and not self.stoprequest.isSet():
            for n in kwargs['nodes']:
                if n['status'] in 'ready':
                    continue
                elif n['status'] == 'provisioned':
                    n['status'] = next_st[n['status']]
                    n['progress'] = 0
                else:
                    n['progress'] += randrange(
                        self.low_tick_count,
                        self.tick_count
                    )
                    if n['progress'] >= 100:
                        n['progress'] = 100
                        n['status'] = next_st[n['status']]
            if error == "deployment":
                shuffle(kwargs['nodes'])
                kwargs['nodes'][0]['status'] = "error"
                kwargs['nodes'][0]['error_type'] = "deploy"
                kwargs['error'] = error_msg
                error = None
            if all(map(
                lambda n: n['progress'] == 100 and n['status'] == 'ready',
                kwargs['nodes']
            )):
                kwargs['status'] = 'ready'
                ready = True
            if any(map(
                lambda n: n['status'] == 'error',
                kwargs['nodes']
            )):
                kwargs['status'] = 'error'
                ready = True
            # TEST: set task to ready no matter what
            if task_ready:
                kwargs['status'] = 'ready'
            yield kwargs
            self.sleep(self.tick_interval)

    def run(self):
        super(FakeDeploymentThread, self).run()
        if settings.FAKE_TASKS_AMQP:
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
            with Connection('amqp://guest:guest@localhost//') as conn:
                with conn.Producer(serializer='json') as producer:
                    for msg in self.message_gen():
                        producer.publish(
                            {
                                "method": self.respond_to,
                                "args": msg
                            },
                            exchange=nailgun_exchange,
                            routing_key='nailgun',
                            declare=[nailgun_queue]
                        )
        else:
            receiver = NailgunReceiver
            receiver.initialize()
            resp_method = getattr(receiver, self.respond_to)
            for msg in self.message_gen():
                resp_method(**msg)
            receiver.stop()


class FakeProvisionThread(FakeThread):
    def run(self):
        super(FakeProvisionThread, self).run()
        receiver = NailgunReceiver
        receiver.initialize()

        # Since we just add systems to cobbler and reboot nodes
        # We think this task is always successful if it is launched.
        kwargs = {
            'task_uuid': self.task_uuid,
            'status': 'ready',
            'progress': 100
        }

        tick_interval = int(settings.FAKE_TASKS_TICK_INTERVAL) or 3
        resp_method = getattr(receiver, self.respond_to)
        resp_method(**kwargs)
        orm = make_session()
        receiver.stop()


class FakeDeletionThread(FakeThread):
    def run(self):
        super(FakeDeletionThread, self).run()
        receiver = NailgunReceiver
        receiver.initialize()
        kwargs = {
            'task_uuid': self.task_uuid,
            'nodes': self.data['args']['nodes'],
            'status': 'ready'
        }
        nodes_to_restore = self.data['args'].get('nodes_to_restore', [])
        tick_interval = int(settings.FAKE_TASKS_TICK_INTERVAL) or 3
        resp_method = getattr(receiver, self.respond_to)
        resp_method(**kwargs)
        orm = make_session()

        for node_data in nodes_to_restore:
            node = Node(**node_data)

            # Offline node just deleted from db
            # and could not recreated with status
            # discover
            if not node.online:
                continue

            node.status = 'discover'
            orm.add(node)
            orm.commit()
            node.attributes = NodeAttributes(node_id=node.id)
            node.attributes.volumes = node.volume_manager.gen_volumes_info()
            network_manager = NetworkManager(db=orm)
            network_manager.update_interfaces_info(node)
            orm.commit()

            ram = round(node.meta.get('ram') or 0, 1)
            cores = node.meta.get('cores') or 'unknown'
            notifier.notify("discover",
                            "New node with %s CPU core(s) "
                            "and %s GB memory is discovered" %
                            (cores, ram), node_id=node.id)
        receiver.stop()


class FakeVerificationThread(FakeThread):
    def run(self):
        super(FakeVerificationThread, self).run()
        receiver = NailgunReceiver
        receiver.initialize()
        kwargs = {
            'task_uuid': self.task_uuid,
            'progress': 0
        }

        tick_count = int(settings.FAKE_TASKS_TICK_COUNT) or 10
        tick_interval = int(settings.FAKE_TASKS_TICK_INTERVAL) or 3
        low_tick_count = tick_count - 20
        if low_tick_count < 0:
            low_tick_count = 0

        resp_method = getattr(receiver, self.respond_to)
        kwargs['progress'] = 0
        timeout = 30
        timer = time.time()
        ready = False

        # some kinda hack for debugging in fake tasks:
        # verification will fail if you specified 404 as VLAN id in any net
        for n in self.data['args']['nodes']:
            for iface in n['networks']:
                if 404 in iface['vlans']:
                    iface['vlans'] = list(set(iface['vlans']) ^ set([404]))

        while not ready and not self.stoprequest.isSet():
            kwargs['progress'] += randrange(
                low_tick_count,
                tick_count
            )
            if kwargs['progress'] >= 100:
                kwargs['progress'] = 100
                kwargs['nodes'] = self.data['args']['nodes']
                kwargs['status'] = 'ready'
                ready = True
            resp_method(**kwargs)
            if time.time() - timer > timeout:
                raise Exception("Timeout exceed")
            self.sleep(tick_interval)
        receiver.stop()


FAKE_THREADS = {
    'provision': FakeProvisionThread,
    'deploy': FakeDeploymentThread,
    'remove_nodes': FakeDeletionThread,
    'verify_networks': FakeVerificationThread
}
