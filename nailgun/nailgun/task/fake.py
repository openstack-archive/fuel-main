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

        nodes_to_provision = []
        for node in nodes:
            if node.status in ('discover', 'provisioning') or \
                    (node.status == 'error' and
                     node.error_type == 'provision'):
                nodes_to_provision.append(node)

        nodes_with_attrs = []
        for n in nodes:
            n.pending_addition = False
            n.status = 'provisioning'
            web.ctx.orm.add(n)
            web.ctx.orm.commit()
            nodes_with_attrs.append({
                'id': n.id, 'status': n.status, 'uid': n.id,
                'ip': n.ip, 'mac': n.mac, 'role': n.role,
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

                for i in range(1, 10):
                    kwargs['progress'] = i * 10
                    receiver.deploy_resp(**kwargs)
                    time.sleep(3)

                kwargs['progress'] = 100
                kwargs['status'] = 'ready'
                for n in kwargs['nodes']:
                    n['status'] = 'ready'
                receiver.deploy_resp(**kwargs)

        FakeDeploymentThread().start()


class DeletionTask(object):

    @classmethod
    def execute(self, task):
        nodes_to_delete = []
        for node in task.cluster.nodes:
            if node.pending_deletion:
                nodes_to_delete.append({
                    'id': node.id,
                    'uid': node.id
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
