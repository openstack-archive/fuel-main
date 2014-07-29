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
import time

from fuelweb_test.helpers.decorators import log_snapshot_on_error
from fuelweb_test import logger
from fuelweb_test import ostf_test_mapping as map_ostf
from fuelweb_test import settings
from fuelweb_test.settings import DEPLOYMENT_MODE_SIMPLE
from fuelweb_test.tests.base_test_case import SetupEnvironment
from fuelweb_test.tests.base_test_case import TestBasic
from fuelweb_test.tests.test_ceph import CephCompactWithCinder
from fuelweb_test.tests.test_ceph import CephHA

from devops.helpers.helpers import wait
from proboscis import SkipTest
from proboscis import test


@test(groups=["thread_3", "ceph"])
class CephRestart(TestBasic):

    @test(depends_on=[CephCompactWithCinder.ceph_multinode_with_cinder],
          groups=["ceph_multinode_restart"])
    @log_snapshot_on_error
    def ceph_multinode_restart(self):
        """Deploy ceph with cinder in simple mode

        Scenario:
            1. Create cluster
            2. Add 1 node with controller and ceph OSD roles
            3. Add 1 node with compute role
            4. Add 2 nodes with cinder and ceph OSD roles
            5. Deploy the cluster
            7. Warm restart
            8. Check ceph status

        Snapshot None

        """
        if settings.OPENSTACK_RELEASE == settings.OPENSTACK_RELEASE_REDHAT:
            raise SkipTest()

        self.env.revert_snapshot("ceph_multinode_with_cinder")

        cluster_id = self.fuel_web.get_last_created_cluster()

        # Warm restart
        self.fuel_web.warm_restart_nodes(self.env.nodes().slaves[:4])

        self.fuel_web.check_ceph_status(cluster_id)

        try:
            self.fuel_web.run_single_ostf_test(
                cluster_id, test_sets=['smoke'],
                test_name=map_ostf.OSTF_TEST_MAPPING.get(
                    'Create volume and attach it to instance'))
        except AssertionError:
            logger.debug("Test failed from first probe,"
                         " we sleep 60 second try one more time "
                         "and if it fails again - test will fails ")
            time.sleep(60)
            self.fuel_web.run_single_ostf_test(
                cluster_id, test_sets=['smoke'],
                test_name=map_ostf.OSTF_TEST_MAPPING.get(
                    'Create volume and attach it to instance'))

        self.fuel_web.run_ostf(cluster_id=cluster_id)

    @test(depends_on=[CephHA.ceph_ha],
          groups=["ceph_ha_restart"])
    @log_snapshot_on_error
    def ceph_ha_restart(self):
        """Deploy ceph with in HA mode

        Scenario:
            1. Create cluster
            2. Add 3 nodes with controller and ceph OSD roles
            3. Add 1 node with ceph OSD roles
            4. Add 2 nodes with compute and ceph OSD roles
            5. Deploy the cluster
            6. Check ceph status
            7. Cold retsart
            8. Check ceph status

        Snapshot ceph_ha

        """
        if settings.OPENSTACK_RELEASE == settings.OPENSTACK_RELEASE_REDHAT:
            raise SkipTest()

        self.env.revert_snapshot("ceph_ha")

        cluster_id = self.fuel_web.get_last_created_cluster()

        self.fuel_web.check_ceph_status(cluster_id)

        # Run ostf
        self.fuel_web.run_ostf(cluster_id=cluster_id)

        # Destroy osd-node
        self.env.nodes().slaves[5].destroy()

        wait(lambda: not self.fuel_web.get_nailgun_node_by_devops_node(
            self.env.nodes().slaves[5])['online'], timeout=30 * 8)
        offline_nodes = [self.fuel_web.get_nailgun_node_by_devops_node(
            self.env.nodes().slaves[5])['id']]
        self.fuel_web.check_ceph_status(cluster_id, offline_nodes)
        self.fuel_web.run_ostf(cluster_id=cluster_id)

        # Destroy compute node
        self.env.nodes().slaves[4].destroy()

        wait(lambda: not self.fuel_web.get_nailgun_node_by_devops_node(
            self.env.nodes().slaves[4])['online'], timeout=30 * 8)

        offline_nodes.append(self.fuel_web.get_nailgun_node_by_devops_node(
            self.env.nodes().slaves[4])['id'])
        self.fuel_web.check_ceph_status(cluster_id, offline_nodes)

        self.fuel_web.run_ostf(cluster_id=cluster_id, should_fail=1)

        # Cold restart
        self.fuel_web.cold_restart_nodes(self.env.nodes().slaves[:4])
        self.fuel_web.check_ceph_status(cluster_id, offline_nodes)

        # Wait until MySQL Galera is UP on primary controller
        self.fuel_web.wait_mysql_galera_is_up(['slave-01'])

        try:
            self.fuel_web.run_single_ostf_test(
                cluster_id, test_sets=['smoke'],
                test_name=map_ostf.OSTF_TEST_MAPPING.get(
                    'Create volume and attach it to instance'))
        except AssertionError:
            logger.debug("Test failed from first probe,"
                         " we sleep 60 second try one more time "
                         "and if it fails again - test will fails ")
            time.sleep(60)
            self.fuel_web.run_single_ostf_test(
                cluster_id, test_sets=['smoke'],
                test_name=map_ostf.OSTF_TEST_MAPPING.get(
                    'Create volume and attach it to instance'))

        self.fuel_web.run_ostf(cluster_id=cluster_id, should_fail=1)

        self.env.make_snapshot("ceph_ha")


@test(groups=["thread_1"])
class SimpleFlatRestart(TestBasic):

    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["simple_flat_warm_restart"])
    @log_snapshot_on_error
    def simple_flat_warm_restart(self):
        """Cold restart for simple environment

        Scenario:
            1. Create cluster
            2. Add 1 node with controller role
            3. Add 1 node with compute role
            4. Deploy the cluster
            5. Validate cluster was set up correctly, there are no dead
            services, there are no errors in logs
            6. Turn off all nodes
            7. Start all nodes
            8. Run OSTF
            9. Warm restart
            10. Run OSTF

        """
        self.env.revert_snapshot("ready_with_3_slaves")

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE_SIMPLE
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['compute']
            }
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)

        # Warm restart
        self.fuel_web.warm_restart_nodes(self.env.nodes().slaves[:2])

        try:
            self.fuel_web.run_single_ostf_test(
                cluster_id, test_sets=['sanity'],
                test_name=map_ostf.OSTF_TEST_MAPPING.get(
                    'Check that required services are running'))
        except AssertionError:
            logger.debug("Test failed from first probe,"
                         " we sleep 60 second try one more time "
                         "and if it fails again - test will fails ")
            time.sleep(60)
            self.fuel_web.run_single_ostf_test(
                cluster_id, test_sets=['sanity'],
                test_name=map_ostf.OSTF_TEST_MAPPING.get(
                    'Check that required services are running'))

        self.fuel_web.run_ostf(
            cluster_id=cluster_id)
