# -*- coding: utf-8 -*-
import json

from paste.fixture import TestApp
from mock import Mock, patch
from netaddr import IPNetwork, IPAddress
from sqlalchemy.sql import not_

import nailgun
from nailgun.logger import logger
from nailgun.task.helpers import TaskHelper
from nailgun.settings import settings
from nailgun.test.base import BaseHandlers
from nailgun.test.base import fake_tasks
from nailgun.test.base import reverse
from nailgun.api.models import Cluster, Attributes, IPAddr, Task
from nailgun.api.models import Network, NetworkGroup
from nailgun.network.manager import NetworkManager


class TestHandlers(BaseHandlers):

    @fake_tasks(fake_rpc=False, mock_rpc=False)
    @patch('nailgun.rpc.cast')
    def test_deploy_cast_with_right_args(self, mocked_rpc):
        self.env.create(
            cluster_kwargs={
                "mode": "ha",
                "type": "compute"
            },
            nodes_kwargs=[
                {"role": "controller", "pending_addition": True},
                {"role": "controller", "pending_addition": True},
            ]
        )
        cluster_db = self.env.clusters[0]

        cluster_depl_mode = 'ha'

        supertask = self.env.launch_deployment()
        deploy_task_uuid = [x.uuid for x in supertask.subtasks
                            if x.name == 'deployment'][0]

        msg = {'method': 'deploy', 'respond_to': 'deploy_resp',
               'args': {}}
        self.db.add(cluster_db)
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
        provision_nodes = []

        admin_net_id = self.env.network_manager.get_admin_network_id()

        for n in sorted(self.env.nodes, key=lambda n: n.id):

            q = self.db.query(IPAddr).join(Network).\
                filter(IPAddr.node == n.id).filter(
                    not_(IPAddr.network == admin_net_id)
                )

            """
            Here we want to get node IP addresses which belong
            to management and public networks respectively
            """
            node_ip_management, node_ip_public, node_ip_storage = map(
                lambda x: q.filter_by(name=x).first().ip_addr
                + "/" + cluster_attrs[x + '_network_range'].split('/')[1],
                ('management', 'public', 'storage')
            )

            nodes.append({'uid': n.id, 'status': n.status, 'ip': n.ip,
                          'error_type': n.error_type, 'mac': n.mac,
                          'role': n.role, 'id': n.id, 'fqdn': n.fqdn,
                          'progress': 0, 'meta': n.meta, 'online': True,
                          'network_data': [{'brd': '172.16.0.255',
                                            'ip': node_ip_management,
                                            'vlan': 103,
                                            'gateway': '172.16.0.1',
                                            'netmask': '255.255.255.0',
                                            'dev': 'eth0',
                                            'name': 'management'},
                                           {'brd': '240.0.1.255',
                                            'ip': node_ip_public,
                                            'vlan': 104,
                                            'gateway': '240.0.1.1',
                                            'netmask': '255.255.255.0',
                                            'dev': 'eth0',
                                            'name': u'public'},
                                           {'name': u'storage',
                                            'ip': node_ip_storage,
                                            'vlan': 102,
                                            'dev': 'eth0',
                                            'netmask': '255.255.255.0',
                                            'brd': '192.168.0.255',
                                            'gateway': u'192.168.0.1'},
                                           {'vlan': 100,
                                            'name': 'floating',
                                            'dev': 'eth0'},
                                           {'vlan': 101,
                                            'name': 'fixed',
                                            'dev': 'eth0'},
                                           {'name': 'admin',
                                            'dev': 'eth0'}]})

            pnd = {
                'profile': settings.COBBLER_PROFILE,
                'power_type': 'ssh',
                'power_user': 'root',
                'power_address': n.ip,
                'power_pass': settings.PATH_TO_BOOTSTRAP_SSH_KEY,
                'name': TaskHelper.slave_name_by_id(n.id),
                'hostname': n.fqdn,
                'name_servers': '\"%s\"' % settings.DNS_SERVERS,
                'name_servers_search': '\"%s\"' % settings.DNS_SEARCH,
                'netboot_enabled': '1',
                'ks_meta': {
                    'puppet_auto_setup': 1,
                    'puppet_master': settings.PUPPET_MASTER_HOST,
                    'puppet_version': settings.PUPPET_VERSION,
                    'puppet_enable': 0,
                    'mco_auto_setup': 1,
                    'install_log_2_syslog': 1,
                    'mco_pskey': settings.MCO_PSKEY,
                    'mco_vhost': settings.MCO_VHOST,
                    'mco_host': settings.MCO_HOST,
                    'mco_user': settings.MCO_USER,
                    'mco_password': settings.MCO_PASSWORD,
                    'mco_connector': settings.MCO_CONNECTOR,
                    'mco_enable': 1,
                    'ks_spaces': "\"%s\"" % json.dumps(
                        n.attributes.volumes).replace("\"", "\\\""),
                    'auth_key': "\"%s\"" % cluster_attrs.get('auth_key', ''),
                }
            }

            netmanager = NetworkManager()
            netmanager.assign_admin_ips(
                n.id,
                len(n.meta.get('interfaces', []))
            )

            admin_ips = set([i.ip_addr for i in self.db.query(IPAddr).
                            filter_by(node=n.id).
                            filter_by(network=admin_net_id)])

            for i in n.meta.get('interfaces', []):
                if 'interfaces' not in pnd:
                    pnd['interfaces'] = {}
                pnd['interfaces'][i['name']] = {
                    'mac_address': i['mac'],
                    'static': '0',
                    'netmask': settings.ADMIN_NETWORK['netmask'],
                    'ip_address': admin_ips.pop(),
                }
                if 'interfaces_extra' not in pnd:
                    pnd['interfaces_extra'] = {}
                pnd['interfaces_extra'][i['name']] = {
                    'peerdns': 'no',
                    'onboot': 'no'
                }

                if i['mac'] == n.mac:
                    pnd['interfaces'][i['name']]['dns_name'] = n.fqdn
                    pnd['interfaces_extra'][i['name']]['onboot'] = 'yes'

            provision_nodes.append(pnd)

        controller_nodes = filter(
            lambda node: node['role'] == 'controller',
            nodes)
        msg['args']['attributes']['controller_nodes'] = controller_nodes
        msg['args']['nodes'] = nodes

        provision_task_uuid = [x.uuid for x in supertask.subtasks
                               if x.name == 'provision'][0]
        provision_msg = {
            'method': 'provision',
            'respond_to': 'provision_resp',
            'args': {
                'task_uuid': provision_task_uuid,
                'engine': {
                    'url': settings.COBBLER_URL,
                    'username': settings.COBBLER_USER,
                    'password': settings.COBBLER_PASSWORD,
                },
                'nodes': provision_nodes,
            }
        }

        nailgun.task.manager.rpc.cast.assert_called_once_with(
            'naily', [provision_msg, msg])

    @fake_tasks(fake_rpc=False, mock_rpc=False)
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
        self.env.launch_deployment()

        # launch_deployment kicks ClusterChangesHandler
        # which in turns launches DeploymentTaskManager
        # which runs DeletionTask, ProvisionTask and DeploymentTask.
        # DeletionTask is sent to one orchestrator worker and
        # ProvisionTask and DeploymentTask messages are sent to
        # another orchestrator worker.
        # That is why we expect here list of two sets of
        # arguments in mocked nailgun.rpc.cast
        # The first set of args is for deletion task and
        # the second one is for provisioning and deployment.

        # remove_nodes method call [0][0][1]
        n_rpc_remove = nailgun.task.task.rpc.cast. \
            call_args_list[0][0][1]['args']['nodes']
        self.assertEquals(len(n_rpc_remove), 1)
        self.assertEquals(n_rpc_remove[0]['uid'], self.env.nodes[1].id)

        # provision method call [1][0][1][0]
        n_rpc_provision = nailgun.task.manager.rpc.cast. \
            call_args_list[1][0][1][0]['args']['nodes']
        # Nodes will be appended in provision list if
        # they 'pending_deletion' = False and
        # 'status' in ('discover', 'provisioning') or
        # 'status' = 'error' and 'error_type' = 'provision'
        # So, only one node from our list will be appended to
        # provision list.
        self.assertEquals(len(n_rpc_provision), 1)
        self.assertEquals(
            n_rpc_provision[0]['name'],
            TaskHelper.slave_name_by_id(self.env.nodes[0].id)
        )

        # deploy method call [1][0][1][1]
        n_rpc_deploy = nailgun.task.manager.rpc.cast. \
            call_args_list[1][0][1][1]['args']['nodes']
        self.assertEquals(len(n_rpc_deploy), 1)
        self.assertEquals(n_rpc_deploy[0]['uid'], self.env.nodes[0].id)

    @fake_tasks(fake_rpc=False, mock_rpc=False)
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

        nodes = sorted(cluster_db.nodes, key=lambda n: n.id)
        self.assertEqual(nodes[0].needs_redeploy, True)

        self.env.launch_deployment()
