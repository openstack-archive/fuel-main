#    Copyright 2014 Mirantis, Inc.
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

from proboscis.asserts import assert_equal
from proboscis import SkipTest
from proboscis import test

from fuelweb_test.helpers.decorators import log_snapshot_on_error
from fuelweb_test.settings import DEPLOYMENT_MODE_SIMPLE
from fuelweb_test.settings import DEPLOYMENT_MODE_HA
from fuelweb_test.settings import OPENSTACK_RELEASE
from fuelweb_test.settings import OPENSTACK_RELEASE_REDHAT
from fuelweb_test.tests.base_test_case import SetupEnvironment
from fuelweb_test.tests.base_test_case import TestBasic


@test(groups=["bonding_simple", "bonding"])
class BondingSimple(TestBasic):
    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["deploy_bonding_active_backup"])
    @log_snapshot_on_error
    def deploy_bonding_active_backup(self):
        """Deploy cluster in simple mode with bonding

        Scenario:
            1. Create cluster
            2. Add 1 node with controller role
            3. Add 1 node with compute role
            4. Setup bonding for all interfaces
            4. Deploy the cluster
            5. Run network verification
            6. Run OSTF

        Snapshot deploy_bonding_active_backup

        """

        if OPENSTACK_RELEASE == OPENSTACK_RELEASE_REDHAT:
            raise SkipTest()

        self.env.revert_snapshot("ready_with_3_slaves")

        segment_type = 'gre'

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE_SIMPLE,
            settings={
                "net_provider": 'neutron',
                "net_segment_type": segment_type,
            }
        )
        self.fuel_web.update_nodes(
            cluster_id, {
                'slave-01': ['controller'],
                'slave-02': ['compute']
            }
        )

        raw_data = {
            'mac': None,
            'mode': 'active-backup',
            'name': 'ovs-bond0',
            'slaves': [
                {'name': 'eth4'},
                {'name': 'eth3'},
                {'name': 'eth2'},
                {'name': 'eth1'}
            ],
            'state': None,
            'type': 'bond',
            'assigned_networks': []
        }

        interfaces = {
            'eth0': ['fuelweb_admin'],
            'ovs-bond0': [
                'public',
                'management',
                'storage'
            ]
        }

        nets = self.fuel_web.client.get_networks(cluster_id)['networks']
        vlan_start = 100

        for net in nets:
            net.update({'vlan_start': vlan_start})
            vlan_start += 1
        self.fuel_web.client.update_network(cluster_id, networks=nets)

        nailgun_nodes = self.fuel_web.client.list_cluster_nodes(cluster_id)
        for node in nailgun_nodes:
            self.fuel_web.update_node_networks(
                node['id'], interfaces_dict=interfaces,
                raw_data=raw_data
            )
        self.fuel_web.deploy_cluster_wait(cluster_id)

        cluster = self.fuel_web.client.get_cluster(cluster_id)
        assert_equal(str(cluster['net_provider']), 'neutron')
        assert_equal(str(cluster['net_segment_type']), segment_type)

        #TODO(Tatyana) uncomment when it will be implemented)
        # self.fuel_web.verify_network(cluster_id)

        self.fuel_web.run_ostf(
            cluster_id=cluster_id,
            should_fail=1,
            failed_test_name=['Create volume and attach it to instance'])

        self.env.make_snapshot("deploy_bonding_active_backup")

    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["deploy_bonding_balance_slb"])
    @log_snapshot_on_error
    def deploy_bonding_balance_slb(self):
        """Deploy cluster in simple mode with bonding

        Scenario:
            1. Create cluster
            2. Add 1 node with controller role
            3. Add 1 node with compute role
            4. Setup bonding for all interfaces
            4. Deploy the cluster
            5. Run network verification
            6. Run OSTF

        Snapshot deploy_bonding_balance_slb

        """

        if OPENSTACK_RELEASE == OPENSTACK_RELEASE_REDHAT:
            raise SkipTest()

        self.env.revert_snapshot("ready_with_3_slaves")

        segment_type = 'vlan'

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE_SIMPLE,
            settings={
                "net_provider": 'neutron',
                "net_segment_type": segment_type,
            }
        )
        self.fuel_web.update_nodes(
            cluster_id, {
                'slave-01': ['controller'],
                'slave-02': ['compute']
            }
        )

        raw_data = {
            'mac': None,
            'mode': 'balance-slb',
            'name': 'ovs-bond0',
            'slaves': [
                {'name': 'eth4'},
                {'name': 'eth3'},
                {'name': 'eth2'},
                {'name': 'eth1'}
            ],
            'state': None,
            'type': 'bond',
            'assigned_networks': []
        }

        interfaces = {
            'eth0': ['fuelweb_admin'],
            'ovs-bond0': [
                'public',
                'management',
                'storage',
                'private'
            ]
        }

        nets = self.fuel_web.client.get_networks(cluster_id)['networks']
        vlan_start = 100

        for net in nets:
            net.update({'vlan_start': vlan_start})
            vlan_start += 1
        self.fuel_web.client.update_network(cluster_id, networks=nets)

        nailgun_nodes = self.fuel_web.client.list_cluster_nodes(cluster_id)
        for node in nailgun_nodes:
            self.fuel_web.update_node_networks(
                node['id'], interfaces_dict=interfaces,
                raw_data=raw_data
            )
        self.fuel_web.deploy_cluster_wait(cluster_id)

        cluster = self.fuel_web.client.get_cluster(cluster_id)
        assert_equal(str(cluster['net_provider']), 'neutron')
        assert_equal(str(cluster['net_segment_type']), segment_type)

        #TODO(Tatyana) uncomment when it will be implemented)
        # self.fuel_web.verify_network(cluster_id)

        self.fuel_web.run_ostf(
            cluster_id=cluster_id,
            should_fail=1,
            failed_test_name=['Create volume and attach it to instance'])

        self.env.make_snapshot("deploy_bonding_balance_slb")


@test(groups=["bonding_ha", "bonding"])
class BondingHA(TestBasic):
    @test(depends_on=[SetupEnvironment.prepare_slaves_5],
          groups=["deploy_bonding_ha_active_backup"])
    @log_snapshot_on_error
    def deploy_bonding_ha_active_backup(self):
        """Deploy cluster in HA mode with bonding

        Scenario:
            1. Create cluster
            2. Add 3 nodes with controller role
            3. Add 2 node with compute role
            4. Setup bonding for all interfaces
            4. Deploy the cluster
            5. Run network verification
            6. Run OSTF

        Snapshot deploy_bonding_ha_active_backup

        """

        if OPENSTACK_RELEASE == OPENSTACK_RELEASE_REDHAT:
            raise SkipTest()

        self.env.revert_snapshot("ready_with_5_slaves")

        segment_type = 'vlan'

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE_HA,
            settings={
                "net_provider": 'neutron',
                "net_segment_type": segment_type,
            }
        )
        self.fuel_web.update_nodes(
            cluster_id, {
                'slave-01': ['controller'],
                'slave-02': ['controller'],
                'slave-03': ['controller'],
                'slave-04': ['compute'],
                'slave-05': ['compute']
            }
        )

        raw_data = {
            'mac': None,
            'mode': 'active-backup',
            'name': 'ovs-bond0',
            'slaves': [
                {'name': 'eth4'},
                {'name': 'eth3'},
                {'name': 'eth2'},
                {'name': 'eth1'}
            ],
            'state': None,
            'type': 'bond',
            'assigned_networks': []
        }

        interfaces = {
            'eth0': ['fuelweb_admin'],
            'ovs-bond0': [
                'public',
                'management',
                'storage'
            ]
        }

        nets = self.fuel_web.client.get_networks(cluster_id)['networks']
        vlan_start = 100

        for net in nets:
            net.update({'vlan_start': vlan_start})
            vlan_start += 1
        self.fuel_web.client.update_network(cluster_id, networks=nets)

        nailgun_nodes = self.fuel_web.client.list_cluster_nodes(cluster_id)
        for node in nailgun_nodes:
            self.fuel_web.update_node_networks(
                node['id'], interfaces_dict=interfaces,
                raw_data=raw_data
            )
        self.fuel_web.deploy_cluster_wait(cluster_id)

        cluster = self.fuel_web.client.get_cluster(cluster_id)
        assert_equal(str(cluster['net_provider']), 'neutron')
        assert_equal(str(cluster['net_segment_type']), segment_type)

        #TODO(Tatyana) uncomment when it will be implemented)
        # self.fuel_web.verify_network(cluster_id)

        self.fuel_web.run_ostf(
            cluster_id=cluster_id,
            should_fail=1,
            failed_test_name=['Create volume and attach it to instance'])

        self.env.make_snapshot("deploy_bonding_ha_active_backup")

    @test(depends_on=[SetupEnvironment.prepare_slaves_5],
          groups=["deploy_bonding_ha_balance_slb"])
    @log_snapshot_on_error
    def deploy_bonding_ha_balance_slb(self):
        """Deploy cluster in HA mode with bonding

        Scenario:
            1. Create cluster
            2. Add 3 nodes with controller role
            3. Add 2 node with compute role
            4. Setup bonding for all interfaces
            4. Deploy the cluster
            5. Run network verification
            6. Run OSTF

        Snapshot deploy_bonding_ha_balance_slb

        """

        if OPENSTACK_RELEASE == OPENSTACK_RELEASE_REDHAT:
            raise SkipTest()

        self.env.revert_snapshot("ready_with_5_slaves")

        segment_type = 'gre'

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE_HA,
            settings={
                "net_provider": 'neutron',
                "net_segment_type": segment_type,
            }
        )
        self.fuel_web.update_nodes(
            cluster_id, {
                'slave-01': ['controller'],
                'slave-02': ['controller'],
                'slave-03': ['controller'],
                'slave-04': ['compute'],
                'slave-05': ['compute']
            }
        )

        raw_data = {
            'mac': None,
            'mode': 'balance-slb',
            'name': 'ovs-bond0',
            'slaves': [
                {'name': 'eth4'},
                {'name': 'eth3'},
                {'name': 'eth2'},
                {'name': 'eth1'}
            ],
            'state': None,
            'type': 'bond',
            'assigned_networks': []
        }

        interfaces = {
            'eth0': ['fuelweb_admin'],
            'ovs-bond0': [
                'public',
                'management',
                'storage'
            ]
        }

        nets = self.fuel_web.client.get_networks(cluster_id)['networks']
        vlan_start = 100

        for net in nets:
            net.update({'vlan_start': vlan_start})
            vlan_start += 1
        self.fuel_web.client.update_network(cluster_id, networks=nets)

        nailgun_nodes = self.fuel_web.client.list_cluster_nodes(cluster_id)
        for node in nailgun_nodes:
            self.fuel_web.update_node_networks(
                node['id'], interfaces_dict=interfaces,
                raw_data=raw_data
            )
        self.fuel_web.deploy_cluster_wait(cluster_id)

        cluster = self.fuel_web.client.get_cluster(cluster_id)
        assert_equal(str(cluster['net_provider']), 'neutron')
        assert_equal(str(cluster['net_segment_type']), segment_type)

        #TODO(Tatyana) uncomment when it will be implemented)
        # self.fuel_web.verify_network(cluster_id)

        self.fuel_web.run_ostf(
            cluster_id=cluster_id,
            should_fail=1,
            failed_test_name=['Create volume and attach it to instance'])

        self.env.make_snapshot("deploy_bonding_ha_balance_slb")
