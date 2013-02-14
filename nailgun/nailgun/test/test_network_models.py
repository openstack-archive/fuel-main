import json

from nailgun.test.base import BaseHandlers
from nailgun.api.models import Vlan, Network, NetworkGroup


class TestNetworkModels(BaseHandlers):

    def test_network_group_size_of_1_creates_1_network(self):
        cluster = self.env.create_cluster(api=False)
        kw = {'release': cluster.release_id,
              'cidr': '10.0.0.0/24',
              'network_size': 256,
              'name': 'fixed',
              'access': 'private',
              'vlan_start': 200,
              'cluster_id': cluster.id}
        ng = NetworkGroup(**kw)
        self.db.add(ng)
        self.db.commit()
        ng.create_networks()
        nets_db = self.db.query(Network).all()
        self.assertEquals(len(nets_db), 1)
        self.assertEquals(nets_db[0].vlan_id, kw['vlan_start'])
        self.assertEquals(nets_db[0].name, kw['name'])
        self.assertEquals(nets_db[0].access, kw['access'])
        self.assertEquals(nets_db[0].cidr, kw['cidr'])

    def test_network_group_creates_several_networks(self):
        cluster = self.env.create_cluster(api=False)
        kw = {'release': cluster.release_id,
              'cidr': '10.0.0.0/8',
              'network_size': 256,
              'name': 'fixed',
              'access': 'private',
              'vlan_start': 200,
              'amount': 25,
              'cluster_id': cluster.id}
        ng = NetworkGroup(**kw)
        self.db.add(ng)
        self.db.commit()
        ng.create_networks()
        nets_db = self.db.query(Network).all()
        self.assertEquals(len(nets_db), kw['amount'])
        self.assertEquals(nets_db[0].vlan_id, kw['vlan_start'])
        self.assertEquals(nets_db[kw['amount'] - 1].vlan_id,
                          kw['vlan_start'] + kw['amount'] - 1)
        self.assertEquals(all(x.name == kw['name'] for x in nets_db), True)
        self.assertEquals(all(x.access == kw['access'] for x in nets_db), True)
        vlans_db = self.db.query(Vlan).all()
        self.assertEquals(len(vlans_db), kw['amount'])

    def test_network_group_slices_cidr_for_networks(self):
        cluster = self.env.create_cluster(api=False)
        kw = {'release': cluster.release_id,
              'cidr': '10.0.0.0/8',
              'network_size': 128,
              'name': 'fixed',
              'access': 'private',
              'vlan_start': 200,
              'amount': 2,
              'cluster_id': cluster.id}
        ng = NetworkGroup(**kw)
        self.db.add(ng)
        self.db.commit()
        ng.create_networks()
        nets_db = self.db.query(Network).all()
        self.assertEquals(len(nets_db), kw['amount'])
        self.assertEquals(nets_db[0].cidr, '10.0.0.0/25')
        self.assertEquals(nets_db[1].cidr, '10.0.0.128/25')
        self.db.refresh(ng)
        self.assertEquals(ng.cidr, '10.0.0.0/8')

    def test_network_group_does_not_squeezes_base_cidr(self):
        cluster = self.env.create_cluster(api=False)
        kw = {'release': cluster.release_id,
              'cidr': '172.0.0.0/24',
              'network_size': 64,
              'name': 'fixed',
              'access': 'private',
              'vlan_start': 200,
              'amount': 3,
              'cluster_id': cluster.id}
        ng = NetworkGroup(**kw)
        self.db.add(ng)
        self.db.commit()
        ng.create_networks()
        self.db.refresh(ng)
        self.assertEquals(ng.cidr, "172.0.0.0/24")

    def test_network_group_does_not_squeezes_base_cidr_if_amount_1(self):
        cluster = self.env.create_cluster(api=False)
        kw = {'release': cluster.release_id,
              'cidr': '172.0.0.0/8',
              'network_size': 256,
              'name': 'public',
              'access': 'public',
              'vlan_start': 200,
              'amount': 1,
              'cluster_id': cluster.id}
        ng = NetworkGroup(**kw)
        self.db.add(ng)
        self.db.commit()
        ng.create_networks()
        self.db.refresh(ng)
        self.assertEquals(ng.cidr, "172.0.0.0/8")

    def test_network_group_sets_correct_gateway_for_few_nets(self):
        cluster = self.env.create_cluster(api=False)
        kw = {'release': cluster.release_id,
              'cidr': '10.0.0.0/8',
              'network_size': 128,
              'name': 'fixed',
              'access': 'private',
              'vlan_start': 200,
              'amount': 2,
              'gateway_ip_index': 5,
              'cluster_id': cluster.id}
        ng = NetworkGroup(**kw)
        self.db.add(ng)
        self.db.commit()
        ng.create_networks()
        nets_db = self.db.query(Network).all()
        self.assertEquals(len(nets_db), kw['amount'])
        self.assertEquals(nets_db[0].gateway, "10.0.0.5")
        self.assertEquals(nets_db[1].gateway, "10.0.0.133")
