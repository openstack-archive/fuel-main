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

import itertools
import json

from mock import Mock
from mock import patch
from netaddr import IPAddress
from netaddr import IPNetwork
from netaddr import IPRange
from sqlalchemy import not_

import nailgun
from nailgun.api.models import IPAddr
from nailgun.api.models import IPAddrRange
from nailgun.api.models import Network
from nailgun.api.models import NetworkGroup
from nailgun.api.models import NodeNICInterface
from nailgun.api.models import Vlan
from nailgun.settings import settings
from nailgun.test.base import BaseHandlers
from nailgun.test.base import fake_tasks
from nailgun.test.base import reverse


class TestNetworkManager(BaseHandlers):

    @fake_tasks(fake_rpc=False, mock_rpc=False)
    @patch('nailgun.rpc.cast')
    def test_assign_ips(self, mocked_rpc):
        self.env.create(
            cluster_kwargs={},
            nodes_kwargs=[
                {"pending_addition": True, "api": True},
                {"pending_addition": True, "api": True}
            ]
        )

        nailgun.task.task.Cobbler = Mock()

        self.env.network_manager.assign_ips(
            [n.id for n in self.env.nodes],
            "management"
        )

        management_net = self.db.query(Network).join(NetworkGroup).\
            filter(
                NetworkGroup.cluster_id == self.env.clusters[0].id
            ).filter_by(
                name='management'
            ).first()

        assigned_ips = []
        for node in self.env.nodes:
            ips = self.db.query(IPAddr).\
                filter_by(node=node.id).\
                filter_by(network=management_net.id).all()

            self.assertEquals(1, len(ips))
            self.assertEquals(
                True,
                self.env.network_manager.check_ip_belongs_to_net(
                    ips[0].ip_addr,
                    management_net
                )
            )
            assigned_ips.append(ips[0].ip_addr)

        # check for uniqueness of IPs:
        self.assertEquals(len(assigned_ips), len(list(set(assigned_ips))))

        # check it doesn't contain broadcast and other special IPs
        net_ip = IPNetwork(management_net.cidr)[0]
        gateway = management_net.gateway
        broadcast = IPNetwork(management_net.cidr)[-1]
        self.assertEquals(False, net_ip in assigned_ips)
        self.assertEquals(False, gateway in assigned_ips)
        self.assertEquals(False, broadcast in assigned_ips)

    @fake_tasks(fake_rpc=False, mock_rpc=False)
    @patch('nailgun.rpc.cast')
    def test_assign_ips_idempotent(self, mocked_rpc):
        self.env.create(
            cluster_kwargs={},
            nodes_kwargs=[
                {
                    "pending_addition": True,
                    "api": True,
                    "status": "error"
                }
            ]
        )

        node_db = self.env.nodes[0]

        self.env.network_manager.assign_ips(
            [node_db.id],
            "management"
        )
        self.env.network_manager.assign_ips(
            [node_db.id],
            "management"
        )

        self.db.refresh(node_db)

        self.assertEquals(
            len(
                filter(
                    lambda n: n['name'] == 'management',
                    self.env.network_manager.get_node_networks(
                        node_db.id
                    )
                )
            ),
            1
        )

    def test_get_default_nic_networkgroups(self):
        cluster = self.env.create_cluster(api=True)
        node = self.env.create_node(api=True)
        node_db = self.env.nodes[0]

        main_nic_id = self.env.network_manager.get_main_nic(node_db.id)
        other_iface = self.db.query(NodeNICInterface).filter_by(
            node_id=node['id']
        ).filter(
            not_(NodeNICInterface.mac == node_db.mac)
        ).first()

        self.app.put(
            reverse('NodeCollectionHandler'),
            json.dumps([{
                'mac': other_iface.mac,
                'meta': node_db.meta,
                'is_agent': True,
                'cluster_id': cluster["id"]
            }]),
            headers=self.default_headers,
            expect_errors=True
        )

        new_main_nic_id = self.env.network_manager.get_main_nic(node_db.id)
        self.assertEquals(new_main_nic_id, other_iface.id)
        self.assertEquals(
            [n.id for n in other_iface.assigned_networks],
            self.env.network_manager.get_default_nic_networkgroups(
                node_db.id,
                other_iface.id
            )
        )
        self.assertEquals(
            self.db.query(NodeNICInterface).get(main_nic_id).assigned_networks,
            []
        )

    def test_assign_vip_is_idempotent(self):
        cluster = self.env.create_cluster(api=True)
        vip = self.env.network_manager.assign_vip(
            cluster['id'],
            "management"
        )
        vip2 = self.env.network_manager.assign_vip(
            cluster['id'],
            "management"
        )
        self.assertEquals(vip, vip2)

    def test_get_node_networks_for_vlan_manager(self):
        self.env.create(
            cluster_kwargs={'net_manager': 'VlanManager'},
            nodes_kwargs=[
                {"pending_addition": True},
            ]
        )

        network_data = self.env.network_manager.get_node_networks(
            self.env.nodes[0].id
        )

        self.assertEquals(len(network_data), 5)
        fixed_nets = filter(lambda net: net['name'] == 'fixed', network_data)
        self.assertEquals(fixed_nets, [])

    def test_nets_empty_list_if_node_does_not_belong_to_cluster(self):
        node = self.env.create_node(api=False)
        network_data = self.env.network_manager.get_node_networks(node.id)
        self.assertEquals(network_data, [])

    def test_assign_admin_ips(self):
        node = self.env.create_node()
        self.env.network_manager.assign_admin_ips(node.id, 2)
        admin_net_id = self.env.network_manager.get_admin_network_id()

        admin_ips = self.db.query(IPAddr).\
            filter_by(node=node.id).\
            filter_by(network=admin_net_id).all()
        self.assertEquals(len(admin_ips), 2)
        map(
            lambda x: self.assertIn(
                IPAddress(x.ip_addr),
                IPRange(
                    settings.ADMIN_NETWORK['first'],
                    settings.ADMIN_NETWORK['last']
                )
            ),
            admin_ips
        )

    def test_assign_admin_ips_large_range(self):
        map(self.db.delete, self.db.query(IPAddrRange).all())
        admin_net_id = self.env.network_manager.get_admin_network_id()
        admin_ng = self.db.query(Network).get(admin_net_id).network_group
        mock_range = IPAddrRange(
            first='10.0.0.1',
            last='10.255.255.254',
            network_group_id=admin_ng.id
        )
        self.db.add(mock_range)
        self.db.commit()
        # Creating two nodes
        n1 = self.env.create_node()
        n2 = self.env.create_node()
        nc = zip([n1.id, n2.id], [2048, 2])

        # Assinging admin IPs on created nodes
        map(lambda (n, c): self.env.network_manager.assign_admin_ips(n, c), nc)

        # Asserting count of admin node IPs
        def asserter(x):
            n, c = x
            l = len(self.db.query(IPAddr).filter_by(network=admin_net_id).
                    filter_by(node=n).all())
            self.assertEquals(l, c)
        map(asserter, nc)

    def test_assign_admin_ips_idempotent(self):
        node = self.env.create_node()
        self.env.network_manager.assign_admin_ips(node.id, 2)
        admin_net_id = self.env.network_manager.get_admin_network_id()
        admin_ips = set([i.ip_addr for i in self.db.query(IPAddr).
                         filter_by(node=node.id).
                         filter_by(network=admin_net_id).all()])
        self.env.network_manager.assign_admin_ips(node.id, 2)
        admin_ips2 = set([i.ip_addr for i in self.db.query(IPAddr).
                          filter_by(node=node.id).
                          filter_by(network=admin_net_id).all()])
        self.assertEquals(admin_ips, admin_ips2)

    def test_assign_admin_ips_only_one(self):
        map(self.db.delete, self.db.query(IPAddrRange).all())
        admin_net_id = self.env.network_manager.get_admin_network_id()
        admin_ng = self.db.query(Network).get(admin_net_id).network_group
        mock_range = IPAddrRange(
            first='10.0.0.1',
            last='10.0.0.1',
            network_group_id=admin_ng.id
        )
        self.db.add(mock_range)
        self.db.commit()

        node = self.env.create_node()
        self.env.network_manager.assign_admin_ips(node.id, 1)

        admin_net_id = self.env.network_manager.get_admin_network_id()

        admin_ips = self.db.query(IPAddr).\
            filter_by(node=node.id).\
            filter_by(network=admin_net_id).all()
        self.assertEquals(len(admin_ips), 1)
        self.assertEquals(admin_ips[0].ip_addr, '10.0.0.1')

    def test_vlan_set_null(self):
        self.env.create_cluster(api=True)
        cluster_db = self.env.clusters[0]
        same_vlan = 100
        resp = self.app.get(
            reverse(
                'NetworkConfigurationHandler',
                kwargs={'cluster_id': cluster_db.id}),
            headers=self.default_headers
        )
        networks_data = json.loads(resp.body)
        same_vlan_nets = filter(
            lambda n: n['vlan_start'] == same_vlan, networks_data['networks'])
        different_vlan_nets = filter(
            lambda n: n['vlan_start'] != same_vlan, networks_data['networks'])
        different_vlan_nets[0]['vlan_start'] = same_vlan
        same_vlan_nets_count_expect = len(same_vlan_nets) + 1
        resp = self.app.put(
            reverse(
                'NetworkConfigurationHandler',
                kwargs={"cluster_id": cluster_db.id}
            ),
            json.dumps(networks_data),
            headers=self.default_headers
        )
        resp = self.app.get(
            reverse(
                'NetworkConfigurationHandler',
                kwargs={'cluster_id': cluster_db.id}),
            headers=self.default_headers
        )
        networks_data = json.loads(resp.body)['networks']
        same_vlan_nets = [
            net for net in networks_data if net["vlan_start"] == same_vlan
        ]
        self.assertEquals(len(same_vlan_nets), same_vlan_nets_count_expect)

        vlan_db = self.db.query(Vlan).get(same_vlan)
        self.assertEquals(len(vlan_db.network), same_vlan_nets_count_expect)

        for net in vlan_db.network:
            self.db.delete(net)
        self.db.commit()
        self.db.refresh(vlan_db)
        self.assertEquals(vlan_db.network, [])

    @fake_tasks(fake_rpc=False, mock_rpc=False)
    @patch('nailgun.rpc.cast')
    def test_admin_ip_cobbler(self, mocked_rpc):
        self.env.create(
            cluster_kwargs={},
            nodes_kwargs=[
                {
                    "api": True,
                    "pending_addition": True,
                    "mac": "00:00:00:00:00:00",
                    "meta": {
                        "interfaces": [
                            {
                                "name": "eth0",
                                "mac": "00:00:00:00:00:00",
                            },
                            {
                                "name": "eth1",
                                "mac": "00:00:00:00:00:01",
                            }
                        ]
                    }
                },
                {
                    "api": True,
                    "pending_addition": True,
                    "mac": "00:00:00:00:00:02",
                    "meta": {
                        "interfaces": [
                            {
                                "name": "eth0",
                                "mac": "00:00:00:00:00:02",
                            },
                            {
                                "name": "eth1",
                                "mac": "00:00:00:00:00:03",
                            }
                        ]
                    }
                }
            ]
        )

        self.env.launch_deployment()
        rpc_nodes_provision = nailgun.task.manager.rpc.cast. \
            call_args_list[0][0][1][0]['args']['nodes']

        map(
            lambda (x, y): self.assertIn(
                IPAddress(
                    rpc_nodes_provision[x]['interfaces'][y]['ip_address']
                ),
                IPRange(
                    settings.ADMIN_NETWORK['first'],
                    settings.ADMIN_NETWORK['last']
                )
            ),
            itertools.product((0, 1), ('eth0', 'eth1'))
        )
