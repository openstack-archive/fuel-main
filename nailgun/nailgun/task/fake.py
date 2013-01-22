import web
import time
import logging
import threading
from random import randrange

from sqlalchemy.orm import object_mapper, ColumnProperty, \
    scoped_session, sessionmaker
from nailgun.db import NoCacheQuery, orm, engine
from nailgun.settings import settings
from nailgun.notifier import notifier
from nailgun.api.models import Network, Node
from nailgun.task.errors import WrongNodeStatus
from nailgun.network import manager as netmanager
from nailgun.rpc.threaded import NailgunReceiver


class FakeThread(threading.Thread):
    def __init__(self, data=None, group=None, target=None, name=None,
                 verbose=None):
        threading.Thread.__init__(self, group=group, target=target, name=name,
                                  verbose=verbose)
        self.data = data
        self.task_uuid = data['args'].get(
            'task_uuid'
        )
        self.respond_to = data['respond_to']
        self.stoprequest = threading.Event()

    def rude_join(self, timeout=None):
        self.stoprequest.set()
        super(FakeThread, self).join(timeout)


class FakeDeploymentThread(FakeThread):
    def run(self):
        receiver = NailgunReceiver()
        kwargs = {
            'task_uuid': self.task_uuid,
            'nodes': self.data['args']['nodes'],
            'status': 'running'
        }

        tick_count = int(settings.FAKE_TASKS_TICK_COUNT) or 20
        low_tick_count = tick_count - 20
        if low_tick_count < 0:
            low_tick_count = 0
        tick_interval = int(settings.FAKE_TASKS_TICK_INTERVAL) or 3
        resp_method = getattr(receiver, self.respond_to)

        next_st = {
            "discover": "provisioning",
            "provisioning": "provisioned",
            "provisioned": "deploying",
            "deploying": "ready"
        }

        ready = False
        while not ready and not self.stoprequest.isSet():
            for n in kwargs['nodes']:
                if not 'progress' in n:
                    n['progress'] = 0
                elif n['status'] == 'error':
                    n['progress'] = 100
                    continue
                elif n['status'] == 'offline':
                    ready = True
                    break
                elif n['status'] == 'discover':
                    n['status'] = next_st[n['status']]
                    n['progress'] = 0
                elif n['status'] != 'provisioned':
                    n['progress'] += randrange(
                        low_tick_count,
                        tick_count
                    )
                    if n['progress'] >= 100:
                        n['progress'] = 100
                        n['status'] = next_st[n['status']]
            resp_method(**kwargs)
            if all(map(
                lambda n: n['status'] in ('provisioned', 'error'),
                kwargs['nodes']
            )):
                ready = True
            else:
                time.sleep(tick_interval)

        error_nodes = filter(
            lambda n: n['status'] == 'error',
            kwargs['nodes']
        )
        offline_nodes = filter(
            lambda n: n['status'] == 'offline',
            kwargs['nodes']
        )
        if error_nodes:
            kwargs['status'] = 'error'
            kwargs['progress'] = 100
            kwargs['error'] = 'Failed to provision node(s): {0}'.format(
                ",".join([str(n['uid']) for n in error_nodes])
            )
            resp_method(**kwargs)
            return
        if offline_nodes:
            kwargs['status'] = 'error'
            kwargs['progress'] = 100
            kwargs['error'] = 'Cannot deploy offline node(s): {0}'.format(
                ",".join([str(n['uid']) for n in offline_nodes])
            )
            resp_method(**kwargs)
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
                        low_tick_count,
                        tick_count
                    )
                    if n['progress'] >= 100:
                        n['progress'] = 100
                        n['status'] = next_st[n['status']]
            if all(map(
                lambda n: n['progress'] == 100 and n['status'] == 'ready',
                kwargs['nodes']
            )):
                kwargs['status'] = 'ready'
                ready = True
            resp_method(**kwargs)
            time.sleep(tick_interval)


class FakeDeletionThread(FakeThread):
    def run(self):
        receiver = NailgunReceiver()
        kwargs = {
            'task_uuid': self.task_uuid,
            'nodes': self.data['args']['nodes'],
            'status': 'ready'
        }
        nodes_to_restore = self.data['args'].get('nodes_to_restore', [])
        tick_interval = int(settings.FAKE_TASKS_TICK_INTERVAL) or 3
        time.sleep(tick_interval)
        resp_method = getattr(receiver, self.respond_to)
        resp_method(**kwargs)
        orm = scoped_session(
            sessionmaker(bind=engine, query_cls=NoCacheQuery)
        )
        for node in nodes_to_restore:
            orm.add(node)
            orm.commit()
            ram = round(node.info.get('ram') or 0, 1)
            cores = node.info.get('cores') or 'unknown'
            notifier.notify("discover",
                            "New node with %s CPU core(s) "
                            "and %s GB memory is discovered" %
                            (cores, ram), node_id=node.id)


class FakeVerificationThread(FakeThread):
    def run(self):
        receiver = NailgunReceiver()
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
        timeout = 10
        timer = time.time()
        ready = False
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
            time.sleep(tick_interval)


FAKE_THREADS = {
    'deploy': FakeDeploymentThread,
    'remove_nodes': FakeDeletionThread,
    'verify_networks': FakeVerificationThread
}
