import web
import time
import logging
import threading
from random import randrange

from sqlalchemy.orm import object_mapper, ColumnProperty, \
    scoped_session, sessionmaker
from nailgun.db import Query, orm
from nailgun.api.models import engine
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


class FakeDeploymentThread(FakeThread):
    def run(self):
        receiver = NailgunReceiver()
        kwargs = {
            'task_uuid': self.task_uuid,
            'nodes': self.data['args']['nodes'],
            'status': 'running'
        }

        tick_count = int(settings.FAKE_TASKS_TICK_COUNT) or 10
        tick_interval = int(settings.FAKE_TASKS_TICK_INTERVAL) or 3

        next_st = {
            "discover": "provisioning",
            "provisioning": "provisioned",
            "provisioned": "deploying",
            "deploying": "ready"
        }
        ready = False
        while not ready:
            for n in kwargs['nodes']:
                if not 'progress' in n:
                    n['progress'] = 0
                if not (n['status'] == 'discover' and
                        not n['status'] == 'ready'):
                    n['status'] = next_st[n['status']]
                    n['progress'] = 0
                elif n['status'] == 'provisioned':
                    n['status'] = next_st[n['status']]
                    n['progress'] = 0
                else:
                    n['progress'] += randrange(0, tick_count)
                    if n['progress'] >= 100:
                        if n['status'] in ('provisioning', 'deploying'):
                            n['status'] = next_st[n['status']]
                        n['progress'] = 100
            if all(map(
                lambda n: n['progress'] == 100 and n['status'] == 'ready',
                kwargs['nodes']
            )):
                kwargs['status'] = 'ready'
                ready = True
            resp_method = getattr(receiver, self.respond_to)
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
            sessionmaker(bind=engine, query_cls=Query)
        )
        for node in nodes_to_restore:
            orm.add(node)
            orm.commit()


class FakeVerificationThread(FakeThread):
    def run(self):
        receiver = NailgunReceiver()
        kwargs = {
            'task_uuid': self.task_uuid,
            'progress': 0
        }

        tick_count = int(settings.FAKE_TASKS_TICK_COUNT) or 10
        tick_interval = int(settings.FAKE_TASKS_TICK_INTERVAL) or 3

        resp_method = getattr(receiver, self.respond_to)
        for i in range(1, tick_count + 1):
            kwargs['progress'] = 100 * i / tick_count
            resp_method(**kwargs)
            time.sleep(tick_interval)

        kwargs['progress'] = 100
        kwargs['nodes'] = self.data['args']['nodes']
        kwargs['status'] = 'ready'
        resp_method(**kwargs)


FAKE_THREADS = {
    'deploy': FakeDeploymentThread,
    'remove_nodes': FakeDeletionThread,
    'verify_networks': FakeVerificationThread
}
