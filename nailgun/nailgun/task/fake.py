import web
import time
import logging
import threading

from sqlalchemy.orm import object_mapper, ColumnProperty

from nailgun.settings import settings
from nailgun.notifier import notifier
from nailgun.api.models import Network, Node
from nailgun.task.errors import WrongNodeStatus
from nailgun.network import manager as netmanager
from nailgun.rpc.threaded import NailgunReceiver


class DeploymentTask(object):

    @classmethod
    def execute(cls, task):
        task_uuid = task.uuid
        nodes = web.ctx.orm.query(Node).filter_by(
            cluster_id=task.cluster.id,
            pending_deletion=False)

        nodes_with_attrs = []
        for n in nodes:
            n.pending_addition = False
            web.ctx.orm.add(n)
            web.ctx.orm.commit()
            nodes_with_attrs.append({
                'id': n.id, 'status': n.status, 'error_type': n.error_type,
                'uid': n.id, 'ip': n.ip, 'mac': n.mac, 'role': n.role,
                'network_data': netmanager.get_node_networks(n.id)
            })

        class FakeDeploymentThread(threading.Thread):
            def run(self):
                receiver = NailgunReceiver()
                kwargs = {
                    'task_uuid': task_uuid,
                    'nodes': nodes_with_attrs,
                    'progress': 0
                }

                tick_count = settings.FAKE_TASKS_TICK_COUNT or 10
                tick_interval = settings.FAKE_TASKS_TICK_INTERVAL or 3

                for i in range(1, tick_count + 1):
                    if i < tick_count / 2:
                        for n in kwargs['nodes']:
                            if n['status'] == 'discover' or (
                                n['status'] == 'error' and
                                    n['error_type'] == 'provision'):
                                        n['status'] = 'provisioning'
                            elif n['status'] == 'ready':
                                n['status'] = 'deploying'
                    elif i < tick_count:
                        for n in kwargs['nodes']:
                            if n['status'] == 'provisioning':
                                n['status'] = 'deploying'
                    else:
                        kwargs['status'] = 'ready'
                        for n in kwargs['nodes']:
                            if n['status'] == 'deploying':
                                n['status'] = 'ready'

                    kwargs['progress'] = 100 * i / tick_count
                    receiver.deploy_resp(**kwargs)
                    if i < tick_count:
                        time.sleep(tick_interval)

        FakeDeploymentThread().start()


class DeletionTask(object):

    @classmethod
    def execute(self, task):
        nodes_to_delete = []
        nodes_to_restore = []
        for node in task.cluster.nodes:
            if node.pending_deletion:
                nodes_to_delete.append({
                    'id': node.id,
                    'uid': node.id,
                    'status': 'discover'
                })

                new_node = Node()
                for prop in object_mapper(new_node).iterate_properties:
                    if (isinstance(prop, ColumnProperty) and prop.key not in (
                            'id', 'cluster_id', 'role', 'pending_deletion')):
                        setattr(new_node, prop.key, getattr(node, prop.key))
                nodes_to_restore.append(new_node)

        receiver = NailgunReceiver()
        kwargs = {
            'task_uuid': task.uuid,
            'nodes': nodes_to_delete,
            'status': 'ready'
        }
        receiver.remove_nodes_resp(**kwargs)

        for node in nodes_to_restore:
            web.ctx.orm.add(node)
            web.ctx.orm.commit()
            notifier.notify("discover", "New fake node discovered")


class VerifyNetworksTask(object):

    @classmethod
    def execute(self, task):
        task_uuid = task.uuid
        nets_db = web.ctx.orm.query(Network).filter_by(
            cluster_id=task.cluster.id).all()
        vlans_db = [net.vlan_id for net in nets_db]
        iface_db = [{'iface': 'eth0', 'vlans': vlans_db}]
        nodes = [{'networks': iface_db, 'uid': n.id}
                 for n in task.cluster.nodes]

        class FakeVerificationThread(threading.Thread):
            def run(self):
                receiver = NailgunReceiver()
                kwargs = {
                    'task_uuid': task_uuid,
                    'progress': 0
                }

                tick_count = settings.FAKE_TASKS_TICK_COUNT or 10
                tick_interval = settings.FAKE_TASKS_TICK_INTERVAL or 3

                for i in range(1, tick_count + 1):
                    kwargs['progress'] = 100 * i / tick_count
                    receiver.verify_networks_resp(**kwargs)
                    time.sleep(tick_interval)

                kwargs['progress'] = 100
                kwargs['nodes'] = nodes
                kwargs['status'] = 'ready'
                receiver.verify_networks_resp(**kwargs)

        FakeVerificationThread().start()
