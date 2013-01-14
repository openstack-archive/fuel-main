import unittest
import json

from mock import patch
from netaddr import IPNetwork, IPAddress

from nailgun.test.base import BaseHandlers
from nailgun.test.base import reverse
from nailgun.network import manager as netmanager
from nailgun.db import engine
from nailgun.api.models import Network, Node, NetworkElement, NetworkGroup


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
        vip = netmanager.assign_vip(cluster['id'], "management")
        management_net = self.db.query(Network).filter_by(
            cluster_id=cluster['id']).filter_by(
                name='management').first()
        ip_db = IPNetwork(management_net.cidr)[2]
        # TODO(mihgen): we should check DB for correct data!
        #  can't do it now because of issues with orm

    def test_assign_vip_is_idempotent(self):
        cluster = self.create_cluster_api()
        vip = netmanager.assign_vip(cluster['id'], "management")
        vip2 = netmanager.assign_vip(cluster['id'], "management")
        management_net = self.db.query(Network).filter_by(
            cluster_id=cluster['id']).filter_by(
                name='management').first()
        ip_db = IPNetwork(management_net.cidr)[2]
        # This test may fail when we fix orm issues
        # If that happen, the code behavior in netmanager is not idempotent...
        self.assertEquals(str(ip_db), vip)
        self.assertEquals(vip, vip2)

    def test_network_group_size_of_1_creates_1_network(self):
        release = self.create_default_release()
        cluster = self.create_default_cluster()
        cidr = "10.0.0.0/24"
        size_of_net = 256
        name = "fixed"
        access = "private"
        vlan_start = 200
        ng = NetworkGroup(cidr=cidr, size_of_net=size_of_net,
                          name=name, access=access,
                          release=release.id, cluster_id=cluster.id,
                          vlan_start=vlan_start)
        self.db.add(ng)
        self.db.commit()
        ng.create_networks()
        nets_db = self.db.query(Network).all()
        self.assertEquals(len(nets_db), 1)
        self.assertEquals(nets_db[0].vlan_id, vlan_start)
        self.assertEquals(nets_db[0].name, name)
        self.assertEquals(nets_db[0].access, access)
        self.assertEquals(nets_db[0].cidr, cidr)

    def test_network_group_creates_several_networks(self):
        release = self.create_default_release()
        cluster = self.create_default_cluster()
        cidr = "10.0.0.0/8"
        size_of_net = 256
        name = "fixed"
        access = "private"
        vlan_start = 200
        amount = 25
        ng = NetworkGroup(cidr=cidr, size_of_net=size_of_net,
                          name=name, access=access,
                          release=release.id, cluster_id=cluster.id,
                          vlan_start=vlan_start, amount=amount)
        self.db.add(ng)
        self.db.commit()
        ng.create_networks()
        nets_db = self.db.query(Network).all()
        self.assertEquals(len(nets_db), amount)
        self.assertEquals(nets_db[0].vlan_id, vlan_start)
        self.assertEquals(nets_db[amount - 1].vlan_id, vlan_start + amount - 1)
        self.assertEquals(all(x.name == name for x in nets_db), True)
        self.assertEquals(all(x.access == access for x in nets_db), True)

    @unittest.skip("Functionality is not implemented for this yet")
    def test_network_group_slices_cidr_for_networks(self):
        release = self.create_default_release()
        cluster = self.create_default_cluster()
        cidr = "10.0.0.0/8"
        size_of_net = 128
        name = "fixed"
        access = "private"
        vlan_start = 200
        amount = 2
        ng = NetworkGroup(cidr=cidr, size_of_net=size_of_net,
                          name=name, access=access,
                          release=release.id, cluster_id=cluster.id,
                          vlan_start=vlan_start, amount=amount)
        self.db.add(ng)
        self.db.commit()
        ng.create_networks()
        nets_db = self.db.query(Network).all()
        self.assertEquals(len(nets_db), amount)
        self.assertEquals(nets_db[0].cidr, "10.0.0.0/25")
        self.assertEquals(nets_db[1].cidr, "10.0.0.128/25")
