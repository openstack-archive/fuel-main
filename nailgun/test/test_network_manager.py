import json
from netaddr import IPNetwork, IPAddress

from base import BaseHandlers
from base import reverse
from network import manager as netmanager
from api.models import engine
from api.models import Network, Node, IPAddr
from provision import ProvisionFactory
from provision.model.node import Node as ProvisionNode
from provision.model.power import Power as ProvisionPower


class TestNetworkManager(BaseHandlers):
    def test_assign_ips(self):
        cluster = self.create_cluster_api()
        node1 = self.create_default_node(cluster_id=cluster['id'])
        node2 = self.create_default_node(cluster_id=cluster['id'])
        # TODO(mihgen): it should be separeted call of network manager,
        #  not via API. It's impossible now because of issues with web.ctx.orm
        ProvisionFactory.getInstance = self.mock.MagicMock()
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
            ips = self.db.query(IPAddr).filter_by(
                node=node.id).filter_by(
                    network=management_net.id).all()

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
