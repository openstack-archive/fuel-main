import json

from nailgun.test.base import BaseHandlers
from nailgun.api.models import Vlan, Network, NetworkGroup


class TestNetworkModels(BaseHandlers):

    def test_network_group_size_of_1_creates_1_network(self):
        release = self.create_default_release()
        cluster = self.create_default_cluster()
        cidr = "10.0.0.0/24"
        network_size = 256
        name = "fixed"
        access = "private"
        vlan_start = 200
        ng = NetworkGroup(cidr=cidr, network_size=network_size,
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
        network_size = 256
        name = "fixed"
        access = "private"
        vlan_start = 200
        amount = 25
        ng = NetworkGroup(cidr=cidr, network_size=network_size,
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
        vlans_db = self.db.query(Vlan).all()
        self.assertEquals(len(vlans_db), amount)

    def test_network_group_slices_cidr_for_networks(self):
        release = self.create_default_release()
        cluster = self.create_default_cluster()
        cidr = "10.0.0.0/8"
        network_size = 128
        name = "fixed"
        access = "private"
        vlan_start = 200
        amount = 2
        ng = NetworkGroup(cidr=cidr, network_size=network_size,
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
        self.db.refresh(ng)
        self.assertEquals(ng.cidr, "10.0.0.0/24")

    def test_network_group_squeezes_base_cidr(self):
        release = self.create_default_release()
        cluster = self.create_default_cluster()
        cidr = "10.0.0.0/8"
        network_size = 256
        name = "fixed"
        access = "private"
        vlan_start = 200
        amount = 1
        ng = NetworkGroup(cidr=cidr, network_size=network_size,
                          name=name, access=access,
                          release=release.id, cluster_id=cluster.id,
                          vlan_start=vlan_start, amount=amount)
        self.db.add(ng)
        self.db.commit()
        ng.create_networks()
        self.db.refresh(ng)
        self.assertEquals(ng.cidr, "10.0.0.0/24")

    def test_network_group_does_not_squeezes_base_cidr(self):
        release = self.create_default_release()
        cluster = self.create_default_cluster()
        cidr = "172.0.0.0/24"
        network_size = 64
        name = "fixed"
        access = "private"
        vlan_start = 200
        amount = 3
        ng = NetworkGroup(cidr=cidr, network_size=network_size,
                          name=name, access=access,
                          release=release.id, cluster_id=cluster.id,
                          vlan_start=vlan_start, amount=amount)
        self.db.add(ng)
        self.db.commit()
        ng.create_networks()
        self.db.refresh(ng)
        self.assertEquals(ng.cidr, "172.0.0.0/24")

    def test_network_group_sets_correct_gateway_for_few_nets(self):
        release = self.create_default_release()
        cluster = self.create_default_cluster()
        cidr = "10.0.0.0/8"
        network_size = 128
        name = "fixed"
        access = "private"
        vlan_start = 200
        amount = 2
        ng = NetworkGroup(cidr=cidr, network_size=network_size,
                          name=name, access=access,
                          release=release.id, cluster_id=cluster.id,
                          vlan_start=vlan_start, amount=amount,
                          gateway_ip_index=5)
        self.db.add(ng)
        self.db.commit()
        ng.create_networks()
        nets_db = self.db.query(Network).all()
        self.assertEquals(len(nets_db), amount)
        self.assertEquals(nets_db[0].gateway, "10.0.0.5")
        self.assertEquals(nets_db[1].gateway, "10.0.0.133")
