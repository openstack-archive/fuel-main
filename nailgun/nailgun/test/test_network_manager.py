import json
import itertools

from mock import Mock, patch
from netaddr import IPNetwork, IPAddress, iter_iprange

import nailgun
from nailgun.test.base import BaseHandlers
from nailgun.test.base import reverse
from nailgun.network import manager as netmanager
from nailgun.db import engine
from nailgun.api.models import Node, IPAddr
from nailgun.api.models import Network, NetworkGroup
from nailgun.settings import settings


class TestNetworkManager(BaseHandlers):

    @patch('nailgun.rpc.cast')
    def test_assign_ips(self, mocked_rpc):
        self.env.create(
            cluster_kwargs={},
            nodes_kwargs=[
                {"pending_addition": True},
                {"pending_addition": True}
            ]
        )
        # TODO(mihgen): it should be separeted call of network manager,
        #  not via API. It's impossible now because of issues with web.ctx.orm

        nailgun.task.task.Cobbler = Mock()
        nailgun.task.task.DeploymentTask._syslog_dir = Mock()
        self.env.launch_deployment()

        nodes = self.db.query(Node).filter_by(
            cluster_id=self.env.clusters[0].id
        ).all()

        management_net = self.db.query(Network).join(NetworkGroup).\
            filter(
                NetworkGroup.cluster_id == self.env.clusters[0].id
            ).filter_by(
                name='management'
            ).first()

        assigned_ips = []
        for node in nodes:
            ips = self.db.query(IPAddr).\
              filter_by(node=node.id).\
              filter_by(network=management_net.id).\
              filter_by(admin=False).all()

            self.assertEquals(1, len(ips))
            self.assertEquals(
                True, IPAddress(ips[0].ip_addr) in
                IPNetwork(management_net.cidr).iter_hosts())
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

    def test_assign_vip(self):
        cluster = self.env.create_cluster(api=True)
        vip = netmanager.assign_vip(cluster['id'], "management")
        management_net = self.db.query(Network).join(NetworkGroup).\
            filter(NetworkGroup.cluster_id == cluster['id']).filter_by(
                name='management').first()
        ip_db = IPNetwork(management_net.cidr)[2]
        # TODO(mihgen): we should check DB for correct data!
        #  can't do it now because of issues with orm

    def test_assign_vip_is_idempotent(self):
        cluster = self.env.create_cluster(api=True)
        vip = netmanager.assign_vip(cluster['id'], "management")
        vip2 = netmanager.assign_vip(cluster['id'], "management")
        self.assertEquals(vip, vip2)

    def test_get_node_networks_for_vlan_manager(self):
        self.env.create(
            cluster_kwargs={'net_manager': 'VlanManager'},
            nodes_kwargs=[
                {"pending_addition": True},
            ]
        )

        network_data = netmanager.get_node_networks(self.env.nodes[0].id)
        self.assertEquals(len(network_data), 4)
        fixed_nets = [x for x in network_data if x['name'] == 'fixed']
        self.assertEquals(fixed_nets, [])

    def test_nets_empty_list_if_node_does_not_belong_to_cluster(self):
        node = self.env.create_node(api=False)
        network_data = netmanager.get_node_networks(node.id)
        self.assertEquals(network_data, [])

    def test_assign_admin_ips(self):
        """
        This test checks nailgun.network.manager.assign_admin_ips method
        """
        node = self.env.create_node()
        netmanager.assign_admin_ips(node.id, 2)

        admin_ips = self.db.query(IPAddr).\
          filter_by(node=node.id).\
          filter_by(admin=True).all()
        self.assertEquals(len(admin_ips), 2)
        map(
            lambda x: self.assertIn(
                IPAddress(x.ip_addr),
                iter_iprange(
                    settings.ADMIN_NETWORK['first'],
                    settings.ADMIN_NETWORK['last']
                )
            ),
            admin_ips
        )

    def test_admin_ip_cobbler(self):
        """
        This test is intended for checking if deployment task
        adds systems to cobbler with multiple interfaces.
        """
        self.env.create(
            cluster_kwargs={},
            nodes_kwargs=[
                {
                    "pending_addition": True,
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
                    "pending_addition": True,
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


        nailgun.task.task.Cobbler = Mock()
        nailgun.task.task.Cobbler().item_from_dict = Mock()
        nailgun.task.task.DeploymentTask._syslog_dir = Mock()
        self.env.launch_deployment()

        map(
            lambda i: self.assertIn(
                IPAddress(
                    nailgun.task.task.Cobbler().item_from_dict.\
                    call_args_list[i[0]][0][2]['interfaces'][i[1]]['ip_address']
                ),
                iter_iprange(
                    settings.ADMIN_NETWORK['first'],
                    settings.ADMIN_NETWORK['last']
                )
            ),
            itertools.product((0, 1), ('eth0', 'eth1'))
        )
