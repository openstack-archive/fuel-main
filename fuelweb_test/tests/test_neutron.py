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
from fuelweb_test.models.fuel_web_client \
    import DEPLOYMENT_MODE_SIMPLE, DEPLOYMENT_MODE_HA
from fuelweb_test.helpers.decorators import debug, log_snapshot_on_error
from fuelweb_test.settings import OPENSTACK_RELEASE, OPENSTACK_RELEASE_REDHAT
from fuelweb_test.tests.base_test_case import TestBasic, SetupEnvironment

logger = logging.getLogger(__name__)
logwrap = debug(logger)


@test
class NeutronGre(TestBasic):

    @log_snapshot_on_error
    @test(groups=["thread_3"], depends_on=[SetupEnvironment.prepare_slaves_3])
    def deploy_neutron_gre(self):

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
                'slave-04': ['compute'],
                'slave-05': ['compute']
            }
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)

        cluster = self.client.get_cluster(cluster_id)
        assert_equal(str(cluster['net_provider']), 'neutron')
        assert_equal(str(cluster['net_segment_type']), segment_type)

        self.env.make_snapshot("deploy_neutron_gre")


@test
class NeutronVlan(TestBasic):

    @log_snapshot_on_error
    @test(groups=["thread_3"], depends_on=[SetupEnvironment.prepare_slaves_3])
    def deploy_neutron_vlan(self):

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
                'slave-04': ['compute'],
                'slave-05': ['compute']
            }
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)

        cluster = self.client.get_cluster(cluster_id)
        assert_equal(str(cluster['net_provider']), 'neutron')
        assert_equal(str(cluster['net_segment_type']), segment_type)

        self.env.make_snapshot("deploy_neutron_vlan")


@test
class NeutronGreHa(TestBasic):

    @log_snapshot_on_error
    @test(groups=["thread_3"], depends_on=[SetupEnvironment.prepare_slaves_5])
    def deploy_neutron_gre_ha(self):

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

        cluster = self.client.get_cluster(cluster_id)
        assert_equal(str(cluster['net_provider']), 'neutron')
        assert_equal(str(cluster['net_segment_type']), segment_type)

        self.env.make_snapshot("deploy_neutron_gre_ha")


@test
class NeutronVlanHa(TestBasic):

    @log_snapshot_on_error
    @test(groups=["thread_3"], depends_on=[SetupEnvironment.prepare_slaves_5])
    def deploy_neutron_vlan_ha(self):

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

        cluster = self.client.get_cluster(cluster_id)
        assert_equal(str(cluster['net_provider']), 'neutron')
        assert_equal(str(cluster['net_segment_type']), segment_type)

        self.env.make_snapshot("deploy_neutron_vlan_ha")
