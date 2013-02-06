import json

from mock import patch
from netaddr import IPNetwork, IPAddress

from nailgun.test.base import BaseHandlers
from nailgun.test.base import reverse
from nailgun.network import manager as netmanager
from nailgun.db import engine
from nailgun.api.models import Node, IPAddr
from nailgun.api.models import Network, NetworkGroup


class TestNetworkManager(BaseHandlers):

    @patch('nailgun.rpc.cast')
    def test_assign_ips(self, mocked_rpc):
        cluster = self.create_cluster_api()
        node1 = self.create_default_node(cluster_id=cluster['id'],
                                         pending_addition=True)
        node2 = self.create_default_node(cluster_id=cluster['id'],
                                         pending_addition=True)
        # TODO(mihgen): it should be separeted call of network manager,
        #  not via API. It's impossible now because of issues with web.ctx.orm

        with patch('nailgun.task.task.Cobbler'):
            resp = self.app.put(
                reverse(
                    'ClusterChangesHandler',
                    kwargs={'cluster_id': cluster['id']}),
                headers=self.default_headers
            )
            self.assertEquals(200, resp.status)

        nodes = self.db.query(Node).filter_by(cluster_id=cluster['id']).all()

        management_net = self.db.query(Network).join(NetworkGroup).\
            filter(NetworkGroup.cluster_id == cluster['id']).filter_by(
                name='management').first()

        assigned_ips = []
        for node in nodes:
            ips = [x for x in self.db.query(IPAddr).filter_by(
                node=node.id).filter_by(
                    network=management_net.id).all() if x.ip_addr]

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
        cluster = self.create_cluster_api()
        vip = netmanager.assign_vip(cluster['id'], "management")
        management_net = self.db.query(Network).join(NetworkGroup).\
            filter(NetworkGroup.cluster_id == cluster['id']).filter_by(
                name='management').first()
        ip_db = IPNetwork(management_net.cidr)[2]
        # TODO(mihgen): we should check DB for correct data!
        #  can't do it now because of issues with orm

    def test_assign_vip_is_idempotent(self):
        cluster = self.create_cluster_api()
        vip = netmanager.assign_vip(cluster['id'], "management")
        vip2 = netmanager.assign_vip(cluster['id'], "management")
        management_net = self.db.query(Network).join(NetworkGroup).\
            filter(NetworkGroup.cluster_id == cluster['id']).filter_by(
                name='management').first()
        ip_db = IPNetwork(management_net.cidr)[2]
        # This test may fail when we fix orm issues
        # If that happen, the code behavior in netmanager is not idempotent...
        self.assertEquals(str(ip_db), vip)
        self.assertEquals(vip, vip2)

    def test_get_node_networks_for_vlan_manager(self):
        cluster = self.create_cluster_api(**{'net_manager': 'VlanManager'})
        node1 = self.create_default_node(cluster_id=cluster['id'],
                                         pending_addition=True)

        network_data = netmanager.get_node_networks(node1.id)
        self.assertEquals(len(network_data), 4)
        fixed_nets = [x for x in network_data if x['name'] == 'fixed']
        self.assertEquals(fixed_nets, [])

    def test_nets_empty_list_if_node_does_not_belong_to_cluster(self):
        node = self.create_default_node()
        network_data = netmanager.get_node_networks(node.id)
        self.assertEquals(network_data, [])
