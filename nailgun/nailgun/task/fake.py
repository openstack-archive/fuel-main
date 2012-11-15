import web
import time
import logging
import threading

from nailgun.api.models import Network, Node
from nailgun.task.errors import WrongNodeStatus
from nailgun.network import manager as netmanager
from nailgun.rpc.threaded import NailgunReceiver


class DeploymentTask(object):

    @classmethod
    def execute(cls, task):
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
                    'task_uuid': task.uuid,
                    'nodes': nodes_with_attrs,
                    'progress': 0
                }

                for i in range(1, 11):
                    if i < 5:
                        for n in kwargs['nodes']:
                            if n['status'] == 'discover' or (
                                n['status'] == 'error' and
                                    n['error_type'] == 'provision'):
                                        n['status'] = 'provisioning'
                            elif n['status'] == 'ready':
                                n['status'] = 'deploying'
                    elif i < 10:
                        for n in kwargs['nodes']:
                            if n['status'] == 'provisioning':
                                n['status'] = 'deploying'
                    else:
                        kwargs['status'] = 'ready'
                        for n in kwargs['nodes']:
                            if n['status'] == 'deploying':
                                n['status'] = 'ready'

                    kwargs['progress'] = i * 10
                    receiver.deploy_resp(**kwargs)
                    if i < 10:
                        time.sleep(3)

        FakeDeploymentThread().start()


class DeletionTask(object):

    @classmethod
    def execute(self, task):
        nodes_to_delete = []
        for node in task.cluster.nodes:
            if node.pending_deletion:
                nodes_to_delete.append({
                    'id': node.id,
                    'uid': node.id,
                    'status': 'discover'
                })

        receiver = NailgunReceiver()
        kwargs = {
            'task_uuid': task.uuid,
            'nodes': nodes_to_delete,
            'status': 'ready'
        }
        receiver.remove_nodes_resp(**kwargs)


class VerifyNetworksTask(object):

    @classmethod
    def execute(self, task):
        nets_db = web.ctx.orm.query(Network).filter_by(
            cluster_id=task.cluster.id).all()
        networks = [{
            'id': n.id, 'vlan_id': n.vlan_id, 'cidr': n.cidr}
            for n in nets_db]

        nodes = [{'id': n.id, 'ip': n.ip, 'mac': n.mac, 'uid': n.id}
                 for n in task.cluster.nodes]

        class FakeVerificationThread(threading.Thread):
            def run(self):
                receiver = NailgunReceiver()
                kwargs = {
                    'task_uuid': task.uuid,
                    'networks': networks,
                    'nodes': nodes,
                    'progress': 0
                }

                for i in range(1, 10):
                    kwargs['progress'] = i * 10
                    receiver.verify_networks_resp(**kwargs)
                    time.sleep(3)

                kwargs['progress'] = 100
                kwargs['status'] = 'ready'
                receiver.verify_networks_resp(**kwargs)

        FakeVerificationThread().start()
