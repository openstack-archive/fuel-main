import json
from netaddr import IPNetwork, IPAddress
from mock import patch

from nailgun.test.base import BaseHandlers
from nailgun.test.base import reverse
from nailgun.network import manager as netmanager
from nailgun.api.models import engine
from nailgun.api.models import Network, Node, NetworkElement


class TestNetworkManager(BaseHandlers):

    def test_assign_ips(self):
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

        management_net = self.db.query(Network).filter_by(
            cluster_id=cluster['id']).filter_by(
                name='management').first()

        assigned_ips = []
        for node in nodes:
            ips = [x for x in self.db.query(NetworkElement).filter_by(
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
        node1 = self.create_default_node(cluster_id=cluster['id'],
                                         pending_addition=True)
        node2 = self.create_default_node(cluster_id=cluster['id'],
                                         pending_addition=True)

        ip = netmanager.assign_vip(cluster['id'], "management")
        # TODO(mihgen): we should check DB for correct data!
        #  can't do it now because of issues with orm
        self.assertEquals("172.16.0.2", ip)
