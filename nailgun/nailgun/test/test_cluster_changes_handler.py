# -*- coding: utf-8 -*-

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

from copy import deepcopy
import json
from mock import patch


import nailgun
from nailgun.api.models import IPAddr
from nailgun.api.models import NetworkGroup
from nailgun.api.models import NodeNICInterface
from nailgun.network.manager import NetworkManager
from nailgun.settings import settings
from nailgun.task.helpers import TaskHelper
from nailgun.test.base import BaseHandlers
from nailgun.test.base import fake_tasks
from nailgun.test.base import reverse


class TestHandlers(BaseHandlers):

    @fake_tasks(fake_rpc=False, mock_rpc=False)
    @patch('nailgun.rpc.cast')
    def test_deploy_cast_with_right_args(self, mocked_rpc):
        self.env.create(
            cluster_kwargs={
                'mode': 'ha_compact'
            },
            nodes_kwargs=[
                {'roles': ['controller'], 'pending_addition': True},
                {'roles': ['controller'], 'pending_addition': True},
                {'roles': ['controller', 'cinder'], 'pending_addition': True},
                {'roles': ['compute', 'cinder'], 'pending_addition': True},
                {'roles': ['compute'], 'pending_addition': True},
                {'roles': ['cinder'], 'pending_addition': True}])

        cluster_db = self.env.clusters[0]

        common_attrs = {
            'deployment_mode': 'ha_compact',
            'mountpoints': '1 1\\n2 2\\n',

            'management_vip': '192.168.0.2',
            'public_vip': '172.16.1.2',

            'fixed_network_range': '10.0.0.0/24',
            'management_network_range': '192.168.0.0/24',
            'floating_network_range': ['172.16.0.2-172.16.0.254'],
            'storage_network_range': '192.168.1.0/24',

            'mp': [{'weight': '1', 'point': '1'},
                   {'weight': '2', 'point': '2'}],
            'novanetwork_parameters': {
                'network_manager': 'FlatDHCPManager',
                'network_size': 256
            },

            'management_interface': 'eth0.101',
            'fixed_interface': 'eth0.103',
            'admin_interface': 'eth0',
            'storage_interface': 'eth0.102',
            'public_interface': 'eth0.100',
            'floating_interface': 'eth0.100',

            'master_ip': '127.0.0.1',
            'use_cinder': True,
            'deployment_id': cluster_db.id
        }

        cluster_attrs = cluster_db.attributes.merged_attrs_values()
        common_attrs.update(cluster_attrs)

        # Common attrs calculation
        nodes_list = []
        nodes_db = sorted(cluster_db.nodes, key=lambda n: n.id)
        assigned_ips = {}
        i = 0
        for node in nodes_db:
            node_id = node.id
            for role in sorted(node.roles + node.pending_roles):
                assigned_ips[node_id] = {}
                assigned_ips[node_id]['internal'] = '192.168.0.%d' % (i + 3)
                assigned_ips[node_id]['public'] = '172.16.1.%d' % (i + 3)
                assigned_ips[node_id]['storage'] = '192.168.1.%d' % (i + 2)

                nodes_list.append({
                    'role': role,

                    'internal_address': assigned_ips[node_id]['internal'],
                    'public_address': assigned_ips[node_id]['public'],
                    'storage_address': assigned_ips[node_id]['storage'],

                    'internal_netmask': '255.255.255.0',
                    'public_netmask': '255.255.255.0',
                    'storage_netmask': '255.255.255.0',

                    'uid': str(node_id),
                    'swift_zone': str(node_id),

                    'name': 'node-%d' % node_id,
                    'fqdn': 'node-%d.%s' % (node_id, settings.DNS_DOMAIN)})
            i += 1

        common_attrs['controller_nodes'] = filter(
            lambda node: node['role'] == 'controller',
            deepcopy(nodes_list))

        common_attrs['nodes'] = nodes_list
        common_attrs['nodes'][0]['role'] = 'primary-controller'

        common_attrs['last_controller'] = common_attrs[
            'controller_nodes'][-1]['name']

        # Individual attrs calculation and
        # merging with common attrs
        priority_mapping = {
            'controller': [600, 500, 400],
            'cinder': 700,
            'compute': 700
        }

        deployment_info = []
        for node in nodes_db:
            ips = assigned_ips[node.id]
            for role in sorted(node.roles):
                priority = priority_mapping[role]
                if isinstance(priority, list):
                    priority = priority.pop()

                individual_atts = {
                    'uid': str(node.id),
                    'status': node.status,
                    'role': role,
                    'online': node.online,
                    'fqdn': 'node-%d.%s' % (node.id, settings.DNS_DOMAIN),
                    'priority': priority,

                    'network_data': {
                        'eth0.100': {
                            'interface': 'eth0.100',
                            'ipaddr': ['%s/24' % ips['public']],
                            'gateway': '172.16.1.1',
                            '_name': 'public'},
                        'eth0.101': {
                            'interface': 'eth0.101',
                            'ipaddr': ['%s/24' % ips['internal']],
                            '_name': 'management'},
                        'eth0.102': {
                            'interface': 'eth0.102',
                            'ipaddr': ['%s/24' % ips['storage']],
                            '_name': 'storage'},
                        'eth0.103': {
                            'interface': 'eth0.103',
                            'ipaddr': 'none',
                            '_name': 'fixed'},
                        'lo': {
                            'interface': 'lo',
                            'ipaddr': ['127.0.0.1/8']},
                        'eth1': {
                            'interface': 'eth1',
                            'ipaddr': 'none'},
                        'eth0': {
                            'interface': 'eth0',
                            'ipaddr': 'dhcp',
                            '_name': 'admin'}}}

                individual_atts.update(common_attrs)
                deployment_info.append(individual_atts)

        supertask = self.env.launch_deployment()
        deploy_task_uuid = [x.uuid for x in supertask.subtasks
                            if x.name == 'deployment'][0]

        deployment_msg = {'method': 'deploy',
                          'respond_to': 'deploy_resp',
                          'args': {}}

        deployment_msg['args']['task_uuid'] = deploy_task_uuid
        deployment_msg['args']['deployment_info'] = deployment_info

        provision_nodes = []
        admin_net_id = self.env.network_manager.get_admin_network_id()

        for n in sorted(self.env.nodes, key=lambda n: n.id):
            pnd = {
                'profile': cluster_attrs['cobbler']['profile'],
                'power_type': 'ssh',
                'power_user': 'root',
                'power_address': n.ip,
                'power_pass': settings.PATH_TO_BOOTSTRAP_SSH_KEY,
                'name': TaskHelper.make_slave_name(n.id),
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

        provision_task_uuid = filter(
            lambda t: t.name == 'provision',
            supertask.subtasks)[0].uuid

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

        args, kwargs = nailgun.task.manager.rpc.cast.call_args
        self.assertEquals(len(args), 2)
        self.assertEquals(len(args[1]), 2)
        self.datadiff(args[1][0], provision_msg)
        self.datadiff(args[1][1], deployment_msg)

    @fake_tasks(fake_rpc=False, mock_rpc=False)
    @patch('nailgun.rpc.cast')
    def test_deploy_and_remove_correct_nodes_and_statuses(self, mocked_rpc):
        self.env.create(
            cluster_kwargs={},
            nodes_kwargs=[
                {
                    "pending_addition": True,
                },
                {
                    "status": "error",
                    "pending_deletion": True
                }
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
            TaskHelper.make_slave_name(self.env.nodes[0].id)
        )

        # deploy method call [1][0][1][1]
        n_rpc_deploy = nailgun.task.manager.rpc.cast.call_args_list[
            1][0][1][1]['args']['deployment_info']
        self.assertEquals(len(n_rpc_deploy), 1)
        self.assertEquals(n_rpc_deploy[0]['uid'], str(self.env.nodes[0].id))

    def test_occurs_error_not_enough_ip_addresses(self):
        self.env.create(
            cluster_kwargs={},
            nodes_kwargs=[
                {'pending_addition': True},
                {'pending_addition': True},
                {'pending_addition': True}])

        cluster = self.env.clusters[0]

        public_network = self.db.query(
            NetworkGroup).filter_by(name='public').first()

        net_data = {
            "networks": [{
                'id': public_network.id,
                'ip_ranges': [[
                    '240.0.1.2',
                    '240.0.1.3']]}]}

        self.app.put(
            reverse(
                'NetworkConfigurationHandler',
                kwargs={'cluster_id': cluster.id}),
            json.dumps(net_data),
            headers=self.default_headers,
            expect_errors=True)

        task = self.env.launch_deployment()

        self.assertEquals(task.status, 'error')
        self.assertEquals(
            task.message,
            'Not enough IP addresses. Public network must have at least '
            '3 IP addresses for the current environment.')

    def test_occurs_error_not_enough_free_space(self):
        meta = self.env.default_metadata()
        meta['disks'] = [{
            "model": "TOSHIBA MK1002TS",
            "name": "sda",
            "disk": "sda",
            # 8GB
            "size": 8000000}]

        self.env.create(
            nodes_kwargs=[
                {"meta": meta, "pending_addition": True}
            ]
        )
        node_db = self.env.nodes[0]

        task = self.env.launch_deployment()

        self.assertEquals(task.status, 'error')
        self.assertEquals(
            task.message,
            "Node '%s' has insufficient disk space" %
            node_db.human_readable_name)

    def test_occurs_error_not_enough_controllers_for_multinode(self):
        self.env.create(
            cluster_kwargs={
                'mode': 'multinode'},
            nodes_kwargs=[
                {'roles': ['compute'], 'pending_addition': True}])

        task = self.env.launch_deployment()

        self.assertEquals(task.status, 'error')
        self.assertEquals(
            task.message,
            "Not enough controllers, multinode mode requires at least 1 "
            "controller")

    def test_occurs_error_not_enough_controllers_for_ha(self):
        self.env.create(
            cluster_kwargs={
                'mode': 'ha_compact'},
            nodes_kwargs=[
                {'roles': ['compute'], 'pending_addition': True}])

        task = self.env.launch_deployment()

        self.assertEquals(task.status, 'error')
        self.assertEquals(
            task.message,
            'Not enough controllers, ha_compact '
            'mode requires at least 3 controllers')

    @fake_tasks()
    def test_admin_untagged_intersection(self):
        meta = self.env.default_metadata()
        meta["interfaces"] = [{
            "mac": "00:00:00:00:00:66",
            "max_speed": 1000,
            "name": "eth0",
            "current_speed": 1000
        }, {
            "mac": "00:00:00:00:00:77",
            "max_speed": 1000,
            "name": "eth1",
            "current_speed": None
        }]

        self.env.create(
            nodes_kwargs=[
                {
                    'api': True,
                    'roles': ['controller'],
                    'pending_addition': True,
                    'meta': meta,
                    'mac': "00:00:00:00:00:66"
                }
            ]
        )

        cluster_id = self.env.clusters[0].id
        node_db = self.env.nodes[0]

        nets = self.env.generate_ui_networks(cluster_id)
        for net in nets["networks"]:
            if net["name"] in ["public", "floating"]:
                net["vlan_start"] = None

        resp = self.app.put(
            reverse('NetworkConfigurationHandler', kwargs={
                'cluster_id': cluster_id
            }),
            json.dumps(nets),
            headers=self.default_headers
        )

        main_iface_id = self.env.network_manager.get_main_nic(
            node_db.id
        )
        main_iface_db = self.db.query(NodeNICInterface).get(
            main_iface_id
        )

        assigned_net_names = [
            n.name
            for n in main_iface_db.assigned_networks
        ]
        self.assertIn("public", assigned_net_names)
        self.assertIn("floating", assigned_net_names)

        supertask = self.env.launch_deployment()
        self.env.wait_error(supertask)

        resp = self.app.get(
            reverse('NodeNICsHandler', kwargs={
                'node_id': node_db.id
            }),
            headers=self.default_headers
        )

        ifaces = json.loads(resp.body)

        wrong_nets = filter(
            lambda nic: (nic["name"] in ["public", "floating"]),
            ifaces[0]["assigned_networks"]
        )

        map(
            ifaces[0]["assigned_networks"].remove,
            wrong_nets
        )

        map(
            ifaces[1]["assigned_networks"].append,
            wrong_nets
        )

        resp = self.app.put(
            reverse('NodeCollectionNICsHandler', kwargs={
                'node_id': node_db.id
            }),
            json.dumps([{"interfaces": ifaces, "id": node_db.id}]),
            headers=self.default_headers
        )

        supertask = self.env.launch_deployment()
        self.env.wait_ready(supertask)
