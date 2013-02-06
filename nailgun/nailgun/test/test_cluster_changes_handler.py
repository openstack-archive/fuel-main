# -*- coding: utf-8 -*-
import json
from paste.fixture import TestApp

from mock import Mock, patch
from netaddr import IPNetwork

import nailgun
from nailgun.test.base import BaseHandlers
from nailgun.test.base import reverse
from nailgun.api.models import Cluster, Attributes, IPAddr, Task
from nailgun.api.models import Network, NetworkGroup


class TestHandlers(BaseHandlers):

    @patch('nailgun.rpc.cast')
    def test_deploy_cast_with_right_args(self, mocked_rpc):
        cluster = self.create_cluster_api()
        cluster_db = self.db.query(Cluster).get(cluster['id'])
        cluster_db.mode = 'ha'
        cluster_db.type = 'compute'
        cluster_depl_mode = 'ha_compute'
        self.db.add(cluster_db)
        self.db.commit()

        node1 = self.create_default_node(cluster_id=cluster['id'],
                                         pending_addition=True)
        node2 = self.create_default_node(cluster_id=cluster['id'],
                                         pending_addition=True)

        nailgun.task.task.Cobbler = Mock()
        resp = self.app.put(
            reverse(
                'ClusterChangesHandler',
                kwargs={'cluster_id': cluster['id']}),
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
        response = json.loads(resp.body)
        supertask_uuid = response['uuid']
        supertask = self.db.query(Task).filter_by(
            uuid=supertask_uuid
        ).first()
        deploy_task_uuid = [x.uuid for x in supertask.subtasks
                            if x.name == 'deployment'][0]

        msg = {'method': 'deploy', 'respond_to': 'deploy_resp',
               'args': {}}
        cluster_attrs = cluster_db.attributes.merged_attrs()
        #attrs_db = self.db.query(Attributes).filter_by(
            #cluster_id=cluster['id']).first()
        #cluster_attrs = attrs_db.merged_attrs()

        nets_db = self.db.query(Network).join(NetworkGroup).\
            filter(NetworkGroup.cluster_id == cluster['id']).all()
        for net in nets_db:
            cluster_attrs[net.name + '_network_range'] = net.cidr

        management_net = self.db.query(Network).join(NetworkGroup).\
            filter(NetworkGroup.cluster_id == cluster['id']).filter_by(
                name='management').first()
        management_vip = str(IPNetwork(management_net.cidr)[4])
        public_net = self.db.query(Network).join(NetworkGroup).\
            filter(NetworkGroup.cluster_id == cluster['id']).filter_by(
                name='public').first()
        public_vip = str(IPNetwork(public_net.cidr)[4])
        cluster_attrs['management_vip'] = management_vip
        cluster_attrs['public_vip'] = public_vip
        cluster_attrs['deployment_mode'] = cluster_depl_mode
        cluster_attrs['network_manager'] = "FlatDHCPManager"

        msg['args']['attributes'] = cluster_attrs
        msg['args']['task_uuid'] = deploy_task_uuid
        nodes = []
        for n in (node1, node2):
            node_ips = self.db.query(IPAddr).filter_by(node=n.id).all()
            node_ip = [ne.ip_addr + "/24" for ne in node_ips]
            nodes.append({'uid': n.id, 'status': n.status, 'ip': n.ip,
                          'error_type': n.error_type, 'mac': n.mac,
                          'role': n.role, 'id': n.id, 'fqdn': n.fqdn,
                          'network_data': [{'brd': '172.16.0.255',
                                            'ip': node_ip[0],
                                            'vlan': 103,
                                            'gateway': '172.16.0.1',
                                            'netmask': '255.255.255.0',
                                            'dev': 'eth0',
                                            'name': 'management'},
                                           {'brd': '240.0.1.255',
                                            'ip': node_ip[1],
                                            'vlan': 104,
                                            'gateway': '240.0.1.1',
                                            'netmask': '255.255.255.0',
                                            'dev': 'eth0',
                                            'name': 'public'},
                                           {'vlan': 100,
                                            'name': 'floating',
                                            'dev': 'eth0'},
                                           {'vlan': 101,
                                            'name': 'fixed',
                                            'dev': 'eth0'},
                                           {'vlan': 102,
                                            'name': 'storage',
                                            'dev': 'eth0'}]})
        msg['args']['nodes'] = nodes

        nailgun.task.task.rpc.cast.assert_called_once_with(
            'naily', msg)

    @patch('nailgun.rpc.cast')
    def test_deploy_and_remove_correct_nodes_and_statuses(self, mocked_rpc):
        cluster = self.create_cluster_api()

        n_ready = self.create_default_node(cluster_id=cluster['id'],
                                           status='ready')
        n_added = self.create_default_node(cluster_id=cluster['id'],
                                           pending_addition=True,
                                           status='discover')
        n_removed = self.create_default_node(cluster_id=cluster['id'],
                                             pending_deletion=True,
                                             status='error')

        nailgun.task.task.Cobbler = Mock()
        resp = self.app.put(
            reverse(
                'ClusterChangesHandler',
                kwargs={'cluster_id': cluster['id']}),
            headers=self.default_headers
        )

        # remove_nodes method call
        n_rpc = nailgun.task.task.rpc.cast. \
            call_args_list[0][0][1]['args']['nodes']
        self.assertEquals(len(n_rpc), 1)
        n_removed_rpc = [n for n in n_rpc if n['uid'] == n_removed.id][0]
        # object is found, so we passed the right node for removal
        self.assertIsNotNone(n_removed_rpc)

        # deploy method call
        n_rpc = nailgun.task.task.rpc.cast. \
            call_args_list[1][0][1]['args']['nodes']
        self.assertEquals(len(n_rpc), 2)
        n_provisioned_rpc = [n for n in n_rpc if n['uid'] == n_ready.id][0]
        n_added_rpc = [n for n in n_rpc if n['uid'] == n_added.id][0]

        self.assertEquals(n_provisioned_rpc['status'], 'provisioned')
        self.assertEquals(n_added_rpc['status'], 'provisioning')

    @patch('nailgun.rpc.cast')
    def test_deploy_reruns_after_network_changes(self, mocked_rpc):
        cluster = self.create_cluster_api()
        node1 = self.create_default_node(cluster_id=cluster['id'],
                                         role='controller',
                                         status='ready')
        node2 = self.create_default_node(cluster_id=cluster['id'],
                                         role='compute',
                                         status='ready')

        # for clean experiment
        cluster_db = self.db.query(Cluster).get(cluster['id'])
        cluster_db.clear_pending_changes()
        cluster_db.add_pending_changes('networks')

        self.assertEqual(node1.needs_redeploy, True)
        self.assertEqual(node2.needs_redeploy, True)

        nailgun.task.task.Cobbler = Mock()
        resp = self.app.put(
            reverse(
                'ClusterChangesHandler',
                kwargs={'cluster_id': cluster['id']}),
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
