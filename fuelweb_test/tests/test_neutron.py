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

import logging

from proboscis import test, SkipTest

from proboscis.asserts import assert_equal
from fuelweb_test.helpers.decorators import debug, log_snapshot_on_error
from fuelweb_test.settings import OPENSTACK_RELEASE, OPENSTACK_RELEASE_REDHAT, \
    DEPLOYMENT_MODE_SIMPLE, DEPLOYMENT_MODE_HA
from fuelweb_test.tests.base_test_case import TestBasic, SetupEnvironment

logger = logging.getLogger(__name__)
logwrap = debug(logger)


@test(groups=["thread_3", "neutron"])
class NeutronGre(TestBasic):

    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["deploy_neutron_gre"])
    @log_snapshot_on_error
    def deploy_neutron_gre(self):
        """Deploy cluster in simple mode with Neutron GRE

        Scenario:
            1. Create cluster
            2. Add 1 node with controller role
            3. Add 2 nodes with compute role
            4. Deploy the cluster
            5. Validate cluster network

        Snapshot: deploy_neutron_gre

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
                "net_segment_type": segment_type
            }
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['compute'],
                'slave-03': ['compute']
            }
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)

        cluster = self.fuel_web.client.get_cluster(cluster_id)
        assert_equal(str(cluster['net_provider']), 'neutron')
        assert_equal(str(cluster['net_segment_type']), segment_type)

        # Network verification will be implemented
        # self.fuel_web.verify_network(self.fuel_web.get_last_created_cluster())

        # Run ostf
        self.fuel_web.run_ostf(
            cluster_id=self.fuel_web.get_last_created_cluster(),
            should_fail=2)

        self.env.make_snapshot("deploy_neutron_gre")


@test(groups=["thread_3", "neutron"])
class NeutronVlan(TestBasic):

    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["deploy_neutron_vlan"])
    @log_snapshot_on_error
    def deploy_neutron_vlan(self):
        """Deploy cluster in simple mode with Neutron VLAN

        Scenario:
            1. Create cluster
            2. Add 1 node with controller role
            3. Add 2 nodes with compute role
            4. Deploy the cluster
            5. Validate cluster network

        Snapshot: deploy_neutron_vlan

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
                "net_segment_type": segment_type
            }
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['compute'],
                'slave-03': ['compute']
            }
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)

        cluster = self.fuel_web.client.get_cluster(cluster_id)
        assert_equal(str(cluster['net_provider']), 'neutron')
        assert_equal(str(cluster['net_segment_type']), segment_type)

        # Network verification will be implemented
        # self.fuel_web.verify_network(self.fuel_web.get_last_created_cluster())

        # Run ostf
        self.fuel_web.run_ostf(
            cluster_id=self.fuel_web.get_last_created_cluster(),
            should_fail=2)

        self.env.make_snapshot("deploy_neutron_vlan")


@test(groups=["thread_4", "neutron"])
class NeutronGreHa(TestBasic):

    @test(depends_on=[SetupEnvironment.prepare_slaves_5],
          groups=["deploy_neutron_gre_ha"])
    @log_snapshot_on_error
    def deploy_neutron_gre_ha(self):
        """Deploy cluster in HA mode with Neutron GRE

        Scenario:
            1. Create cluster
            2. Add 3 nodes with controller role
            3. Add 2 nodes with compute role
            4. Deploy the cluster
            5. Validate cluster network

        Snapshot: deploy_neutron_gre_ha

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
                "net_segment_type": segment_type
            }
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['controller'],
                'slave-03': ['controller'],
                'slave-04': ['compute'],
                'slave-05': ['compute']
            }
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)

        cluster = self.fuel_web.client.get_cluster(cluster_id)
        assert_equal(str(cluster['net_provider']), 'neutron')
        assert_equal(str(cluster['net_segment_type']), segment_type)

        # Network verification will be implemented
        # self.fuel_web.verify_network(self.fuel_web.get_last_created_cluster())

        # Run ostf
        self.fuel_web.run_ostf(
            cluster_id=self.fuel_web.get_last_created_cluster(),
            should_fail=4)
        self.env.make_snapshot("deploy_neutron_gre_ha")


@test(groups=["thread_2", "neutron"])
class NeutronVlanHa(TestBasic):

    @test(depends_on=[SetupEnvironment.prepare_slaves_5],
          groups=["deploy_neutron_vlan_ha"])
    @log_snapshot_on_error
    def deploy_neutron_vlan_ha(self):
        """Deploy cluster in HA mode with Neutron VLAN

        Scenario:
            1. Create cluster
            2. Add 3 nodes with controller role
            3. Add 2 nodes with compute role
            4. Deploy the cluster
            5. Validate cluster network

        Snapshot: deploy_neutron_vlan_ha

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
                "net_segment_type": segment_type
            }
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['controller'],
                'slave-03': ['controller'],
                'slave-04': ['compute'],
                'slave-05': ['compute']
            }
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)

        cluster = self.fuel_web.client.get_cluster(cluster_id)
        assert_equal(str(cluster['net_provider']), 'neutron')
        assert_equal(str(cluster['net_segment_type']), segment_type)

        # Network verification will be implemented
        # self.fuel_web.verify_network(self.fuel_web.get_last_created_cluster())

        # Run ostf
        self.fuel_web.run_ostf(
            cluster_id=self.fuel_web.get_last_created_cluster(),
            should_fail=4)

        self.env.make_snapshot("deploy_neutron_vlan_ha")