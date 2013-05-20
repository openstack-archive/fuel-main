# -*- coding: utf-8 -*-
import json
from paste.fixture import TestApp
from mock import Mock, patch
from netaddr import IPNetwork, IPAddress

import nailgun
from nailgun.test.base import BaseHandlers
from nailgun.test.base import reverse
from nailgun.api.models import Cluster, Attributes, IPAddr, Task
from nailgun.api.models import Network, NetworkGroup


class TestHandlers(BaseHandlers):

    @patch('nailgun.rpc.cast')
    def test_deploy_cast_with_right_args(self, mocked_rpc):
        cluster = self.env.create_cluster(
            mode="ha",
            type="compute"
        )
        map(
            lambda x: self.env.create_node(
                api=True,
                cluster_id=cluster['id'],
                **x),
            [
                {"role": "controller", "pending_addition": True},
                {"role": "controller", "pending_addition": True},
            ]
        )
        cluster_db = self.env.clusters[0]

        cluster_depl_mode = 'ha'

        nailgun.task.task.Cobbler = Mock()
        supertask = self.env.launch_deployment()
        deploy_task_uuid = [x.uuid for x in supertask.subtasks
                            if x.name == 'deployment'][0]

        msg = {'method': 'deploy', 'respond_to': 'deploy_resp',
               'args': {}}
        cluster_attrs = cluster_db.attributes.merged_attrs_values()

        nets_db = self.db.query(Network).join(NetworkGroup).\
            filter(NetworkGroup.cluster_id == cluster_db.id).all()
        for net in nets_db:
            cluster_attrs[net.name + '_network_range'] = net.cidr

        management_vip = self.env.network_manager.assign_vip(
            cluster_db.id,
            'management'
        )
        public_vip = self.env.network_manager.assign_vip(
            cluster_db.id,
            'public'
        )

        cluster_attrs['management_vip'] = management_vip
        cluster_attrs['public_vip'] = public_vip
        cluster_attrs['deployment_mode'] = cluster_depl_mode
        cluster_attrs['deployment_id'] = cluster_db.id
        cluster_attrs['network_manager'] = "FlatDHCPManager"

        msg['args']['attributes'] = cluster_attrs
        msg['args']['task_uuid'] = deploy_task_uuid
        nodes = []

        for n in sorted(self.env.nodes, key=lambda n: n.id):

            q = self.db.query(IPAddr).join(Network).\
                filter(IPAddr.node == n.id, False == IPAddr.admin)

            """
            Here we want to get node IP addresses which belong
            to management and public networks respectively
            """
            node_ip_management, node_ip_public = map(
                lambda x: q.filter_by(name=x).first().ip_addr
                + "/" + cluster_attrs[x + '_network_range'].split('/')[1],
                ('management', 'public')
            )

            nodes.append({'uid': n.id, 'status': 'provisioning', 'ip': n.ip,
                          'error_type': n.error_type, 'mac': n.mac,
                          'role': n.role, 'id': n.id, 'fqdn':
                          'slave-%d.example.com' % n.id,
                          'progress': 0, 'meta': n.meta, 'online': True,
                          'network_data': [{'brd': '172.16.0.255',
                                            'ip': node_ip_management,
                                            'vlan': 103,
                                            'gateway': u'172.16.0.1',
                                            'netmask': '255.255.255.0',
                                            'dev': 'eth0',
                                            'name': u'management'},
                                           {'brd': '240.0.1.255',
                                            'ip': node_ip_public,
                                            'vlan': 104,
                                            'gateway': u'240.0.1.1',
                                            'netmask': '255.255.255.0',
                                            'dev': 'eth0',
                                            'name': u'public'},
                                           {'vlan': 100,
                                            'name': u'floating',
                                            'dev': 'eth0'},
                                           {'vlan': 101,
                                            'name': u'fixed',
                                            'dev': 'eth0'},
                                           {'vlan': 102,
                                            'name': u'storage',
                                            'dev': 'eth0'},
                                           {'name': 'admin',
                                            'dev': 'eth0'}]})
        msg['args']['nodes'] = nodes

        nailgun.task.task.rpc.cast.assert_called_once_with(
            'naily', msg)

    @patch('nailgun.rpc.cast')
    def test_deploy_and_remove_correct_nodes_and_statuses(self, mocked_rpc):
        cluster = self.env.create_cluster()
        map(
            lambda x: self.env.create_node(
                api=True,
                cluster_id=cluster['id'],
                **x),
            [
                {"pending_addition": True},
                {"pending_deletion": True, "status": "error"},
            ]
        )
        nailgun.task.task.Cobbler = Mock()
        self.env.launch_deployment()

        # launch_deployment kicks ClusterChangesHandler
        # which in turns launches DeploymentTaskManager
        # which runs DeletionTask and DeploymentTask.
        # That is why we expect here list of two sets of
        # arguments in mocked nailgun.rpc.cast
        # The first set of args is for deletion task and
        # the second one is for deployment.

        # remove_nodes method call
        n_rpc = nailgun.task.task.rpc.cast. \
            call_args_list[0][0][1]['args']['nodes']
        self.assertEquals(len(n_rpc), 1)

        n_removed_rpc = [
            n for n in n_rpc if n['uid'] == self.env.nodes[1].id
        ][0]
        # object is found, so we passed the right node for removal
        self.assertIsNotNone(n_removed_rpc)

        # deploy method call
        n_rpc = nailgun.task.task.rpc.cast. \
            call_args_list[1][0][1]['args']['nodes']
        self.assertEquals(len(n_rpc), 1)

        provisioning_node = filter(
            lambda x: x['uid'] == self.env.nodes[0].id, n_rpc)[0]

        self.assertEquals(provisioning_node['status'], 'provisioning')

    @patch('nailgun.rpc.cast')
    def test_deploy_reruns_after_network_changes(self, mocked_rpc):
        self.env.create(
            cluster_kwargs={},
            nodes_kwargs=[
                {"status": "ready"},
                {
                    "pending_deletion": True,
                    "status": "ready",
                    "role": "compute"
                },
            ]
        )

        # for clean experiment
        cluster_db = self.env.clusters[0]
        cluster_db.clear_pending_changes()
        cluster_db.add_pending_changes('networks')

        for n in self.env.nodes:
            self.assertEqual(n.needs_redeploy, True)

        nailgun.task.task.Cobbler = Mock()
        self.env.launch_deployment()
