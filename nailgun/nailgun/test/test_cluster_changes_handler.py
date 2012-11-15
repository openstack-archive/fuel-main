# -*- coding: utf-8 -*-
import json
from paste.fixture import TestApp

from mock import Mock

import nailgun
from nailgun.test.base import BaseHandlers
from nailgun.test.base import reverse
from nailgun.api.models import Cluster, Attributes, IPAddr, Task


class TestHandlers(BaseHandlers):

    def test_deploy_cast_with_right_args(self):
        nailgun.task.task.rpc = Mock()
        cluster = self.create_cluster_api()
        cluster_db = self.db.query(Cluster).get(cluster['id'])

        attrs = cluster_db.attributes.merged_attrs()
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
        supertask = self.db.query(Task).filter_by(uuid=supertask_uuid).first()
        deploy_task_uuid = [x.uuid for x in supertask.subtasks
                            if x.name == 'deployment'][0]

        msg = {'method': 'deploy', 'respond_to': 'deploy_resp',
               'args': {}}
        attrs_db = self.db.query(Attributes).filter_by(
            cluster_id=cluster['id']).first()
        attrs = attrs_db.merged_attrs()
        msg['args']['attributes'] = attrs
        msg['args']['task_uuid'] = deploy_task_uuid
        nodes = []
        for n in (node1, node2):
            node_ip = str(self.db.query(IPAddr).filter_by(
                node=n.id).first().ip_addr) + '/24'
            nodes.append({'uid': n.id, 'status': n.status, 'ip': n.ip,
                          'mac': n.mac, 'role': n.role, 'id': n.id,
                          'network_data': [{'brd': '172.16.0.255',
                                            'ip': node_ip,
                                            'vlan': 103,
                                            'gateway': '172.16.0.1',
                                            'dev': 'eth0'}]})
        msg['args']['nodes'] = nodes

        nailgun.task.task.rpc.cast.assert_called_once_with(
            'naily', msg)

    def test_deploy_and_remove_cast_with_correct_nodes_and_statuses(self):
        nailgun.task.task.rpc = Mock()
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
        n_ready_rpc = [n for n in n_rpc if n['uid'] == n_ready.id][0]
        n_added_rpc = [n for n in n_rpc if n['uid'] == n_added.id][0]

        self.assertEquals(n_ready_rpc['status'], 'ready')
        self.assertEquals(n_added_rpc['status'], 'provisioning')
