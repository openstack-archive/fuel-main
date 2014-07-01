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

import os

from proboscis.asserts import assert_equal
from proboscis import test

from fuelweb_test.helpers import checkers
from fuelweb_test.helpers.decorators import log_snapshot_on_error
from fuelweb_test.helpers.decorators import create_diagnostic_snapshot
from fuelweb_test import settings as hlp_data
from fuelweb_test.tests import test_simple as simple_data
from fuelweb_test.tests import test_neutron as neutron_data
from fuelweb_test.tests import base_test_case as base_test_data


@test(groups=["upgrade"])
class UpgradeFuelMaster(base_test_data.TestBasic):
    @test(depends_on=[simple_data.SimpleCinder.deploy_simple_cinder],
          groups=["upgrade_simple"])
    @log_snapshot_on_error
    def upgrade_simple_env(self):
        """Upgrade simple deployed cluster

        Scenario:
            1. Revert snapshot with simple sinder env
            2. Run upgrade on master
            3. Check that upgrade was successful
            4. Add another cinder node
            5. Re-deploy cluster
            6. Run OSTF

        """

        self.env.revert_snapshot("deploy_simple_cinder")
        cluster_id = self.fuel_web.get_last_created_cluster()
        checkers.upload_tarball(self.env.get_admin_remote(),
                                hlp_data.UPGRADE_TARBALL_PATH, '/var')
        checkers.check_tarball_exists(self.env.get_admin_remote(),
                                      os.path.basename(hlp_data.
                                                       UPGRADE_TARBALL_PATH),
                                      '/var')
        checkers.untar(self.env.get_admin_remote(),
                       os.path.basename(hlp_data.
                                        UPGRADE_TARBALL_PATH), '/var')
        checkers.run_script(self.env.get_admin_remote(), '/var', 'upgrade.sh')
        checkers.wait_upgrade_is_done(self.env.get_admin_remote(), 1500)
        checkers.check_upgraded_containers(self.env.get_admin_remote(),
                                           hlp_data.UPGRADE_FUEL_FROM,
                                           hlp_data.UPGRADE_FUEL_TO)
        self.fuel_web.assert_nodes_in_ready_state(cluster_id)
        self.fuel_web.assert_fuel_version(hlp_data.UPGRADE_FUEL_TO)
        self.env.bootstrap_nodes(self.env.nodes().slaves[3:4])
        self.fuel_web.update_nodes(
            cluster_id, {'slave-04': ['compute']},
            True, False
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)
        self.fuel_web.assert_cluster_ready(
            'slave-01', smiles_count=8, networks_count=1, timeout=300)
        self.fuel_web.run_ostf(cluster_id=cluster_id)
        create_diagnostic_snapshot(self.env, "pass", "upgrade_simple_env")

        self.env.make_snapshot("upgrade_simple")

    @test(depends_on=[neutron_data.NeutronGreHa.deploy_neutron_gre_ha],
          groups=["upgrade_ha"])
    @log_snapshot_on_error
    def upgrade_ha_env(self):
        """Upgrade ha deployed cluster

        Scenario:
            1. Revert snapshot with neutron gre ha env
            2. Run upgrade on master
            3. Check that upgrade was successful
            4. Check cluster is operable
            5. Create new simple Vlan cluster
            6. Deploy cluster
            7. Run OSTF

        """
        self.env.revert_snapshot("deploy_neutron_gre_ha")
        cluster_id = self.fuel_web.get_last_created_cluster()
        checkers.upload_tarball(self.env.get_admin_remote(),
                                hlp_data.UPGRADE_TARBALL_PATH, '/var')
        checkers.check_tarball_exists(self.env.get_admin_remote(),
                                      os.path.basename(hlp_data.
                                                       UPGRADE_TARBALL_PATH),
                                      '/var')
        checkers.untar(self.env.get_admin_remote(),
                       os.path.basename(hlp_data.
                                        UPGRADE_TARBALL_PATH), '/var')
        checkers.run_script(self.env.get_admin_remote(), '/var', 'upgrade.sh')
        checkers.wait_upgrade_is_done(self.env.get_admin_remote(), 1500)
        checkers.check_upgraded_containers(self.env.get_admin_remote(),
                                           hlp_data.UPGRADE_FUEL_FROM,
                                           hlp_data.UPGRADE_FUEL_TO)
        self.fuel_web.assert_fuel_version(hlp_data.UPGRADE_FUEL_TO)
        self.fuel_web.assert_nodes_in_ready_state(cluster_id)
        self.fuel_web.run_ostf(
            cluster_id=cluster_id,
            should_fail=1,
            failed_test_name=['Create volume and attach it to instance'])

        self.env.bootstrap_nodes(self.env.nodes().slaves[5:7])
        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=hlp_data.DEPLOYMENT_MODE_SIMPLE,
            settings={
                'tenant': 'novaSimpleVlan',
                'user': 'novaSimpleVlan',
                'password': 'novaSimpleVlan'
            }
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-06': ['controller'],
                'slave-07': ['compute']
            }
        )
        self.fuel_web.update_vlan_network_fixed(
            cluster_id, amount=8, network_size=32)
        self.fuel_web.deploy_cluster_wait(cluster_id)
        self.fuel_web.assert_cluster_ready(
            'slave-06', smiles_count=6, networks_count=8, timeout=300)
        task = self.fuel_web.run_network_verify(cluster_id)
        self.fuel_web.assert_task_success(task, 60 * 2, interval=10)

        self.fuel_web.run_ostf(
            cluster_id=cluster_id,
            should_fail=1,
            failed_test_name=['Create volume and attach it to instance'])
        self.env.make_snapshot("upgrade_ha")

    @test(depends_on=[simple_data.SimpleCinder.deploy_simple_cinder],
          groups=["deploy_ha_after_upgrade"])
    @log_snapshot_on_error
    def deploy_ha_after_upgrade(self):
        """Upgrade and deploy new ha cluster

        Scenario:
            1. Revert snapshot with simple cinder env
            2. Run upgrade on master
            3. Check that upgrade was successful
            4. Re-deploy cluster
            5. Run OSTF

        """
        self.env.revert_snapshot("deploy_simple_cinder")
        cluster_id = self.fuel_web.get_last_created_cluster()
        checkers.upload_tarball(self.env.get_admin_remote(),
                                hlp_data.UPGRADE_TARBALL_PATH, '/var')
        checkers.check_tarball_exists(self.env.get_admin_remote(),
                                      os.path.basename(hlp_data.
                                                       UPGRADE_TARBALL_PATH),
                                      '/var')
        checkers.untar(self.env.get_admin_remote(),
                       os.path.basename(hlp_data.
                                        UPGRADE_TARBALL_PATH), '/var')
        checkers.run_script(self.env.get_admin_remote(), '/var', 'upgrade.sh')
        checkers.wait_upgrade_is_done(self.env.get_admin_remote(), 1500)
        checkers.check_upgraded_containers(self.env.get_admin_remote(),
                                           hlp_data.UPGRADE_FUEL_FROM,
                                           hlp_data.UPGRADE_FUEL_TO)
        self.fuel_web.assert_nodes_in_ready_state(cluster_id)
        self.fuel_web.assert_fuel_version(hlp_data.UPGRADE_FUEL_TO)
        self.env.bootstrap_nodes(self.env.nodes().slaves[3:9])
        segment_type = 'vlan'
        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=hlp_data.DEPLOYMENT_MODE_HA,
            settings={
                "net_provider": 'neutron',
                "net_segment_type": segment_type
            }
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-04': ['controller'],
                'slave-05': ['controller'],
                'slave-06': ['controller'],
                'slave-07': ['compute'],
                'slave-08': ['compute'],
                'slave-09': ['cinder']
            }
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)

        cluster = self.fuel_web.client.get_cluster(cluster_id)
        assert_equal(str(cluster['net_provider']), 'neutron')
        self.fuel_web.run_ostf(
            cluster_id=cluster_id,
            should_fail=0)
        self.env.make_snapshot("deploy_ha_after_upgrade")


@test(groups=["rollback"])
class RollbackFuelMaster(base_test_data.TestBasic):
    @test(depends_on=[simple_data.SimpleCinder.deploy_simple_cinder],
          groups=["rollback_manual", "upgrade"])
    @log_snapshot_on_error
    def rollback_simple_env(self):
        """Rollback manually simple deployed cluster

        Scenario:
            1. Revert snapshot with simple sinder env
            2. Run upgrade on master
            3. Check that upgrade was successful
            4. Rollback cluster manually
            5. Check that rollback was successful
            6. Run OSTF

        """
        self.env.revert_snapshot("deploy_simple_cinder")
        cluster_id = self.fuel_web.get_last_created_cluster()
        checkers.upload_tarball(self.env.get_admin_remote(),
                                hlp_data.UPGRADE_TARBALL_PATH, '/var')
        checkers.check_tarball_exists(self.env.get_admin_remote(),
                                      os.path.basename(hlp_data.
                                                       UPGRADE_TARBALL_PATH),
                                      '/var')
        checkers.untar(self.env.get_admin_remote(),
                       os.path.basename(hlp_data.
                                        UPGRADE_TARBALL_PATH), '/var')
        checkers.run_script(self.env.get_admin_remote(), '/var', 'upgrade.sh')
        checkers.wait_upgrade_is_done(self.env.get_admin_remote(), 1500)
        checkers.check_upgraded_containers(self.env.get_admin_remote(),
                                           hlp_data.UPGRADE_FUEL_FROM,
                                           hlp_data.UPGRADE_FUEL_TO)
        self.fuel_web.assert_nodes_in_ready_state(cluster_id)
        self.fuel_web.assert_fuel_version(hlp_data.UPGRADE_FUEL_TO)

        self.fuel_web.manual_rollback(self.env.get_admin_remote(),
                                      hlp_data.UPGRADE_FUEL_FROM)
        self.fuel_web.wait_nodes_get_online_state(self.env.nodes().slaves[:3])
        self.fuel_web.assert_nodes_in_ready_state(cluster_id)
        self.fuel_web.assert_fuel_version(hlp_data.UPGRADE_FUEL_FROM)
        checkers.check_upgraded_containers(self.env.get_admin_remote(),
                                           hlp_data.UPGRADE_FUEL_TO,
                                           hlp_data.UPGRADE_FUEL_FROM)
        self.fuel_web.run_ostf(cluster_id=cluster_id)

        self.env.make_snapshot("rollback_manual")

    @test(depends_on=[neutron_data.NeutronGre.deploy_neutron_gre],
          groups=["rollback_automatic", "upgrade"])
    @log_snapshot_on_error
    def rollback_automatically_simple_env(self):
        """Rollback automatically simple deployed cluster

        Scenario:
            1. Revert snapshot with simple neutron gre env
            2. Add raise exception to docker_engine.py file
            3. Run upgrade on master
            4. Check that rollback starts automatically
            5. Check that cluster was not upgraded and run OSTf
            6. Add 1 cinder node and re-deploy cluster
            7. Run OSTF

        """
        self.env.revert_snapshot("deploy_neutron_gre")
        cluster_id = self.fuel_web.get_last_created_cluster()
        checkers.upload_tarball(self.env.get_admin_remote(),
                                hlp_data.UPGRADE_TARBALL_PATH, '/var')
        checkers.check_tarball_exists(self.env.get_admin_remote(),
                                      os.path.basename(hlp_data.
                                                       UPGRADE_TARBALL_PATH),
                                      '/var')
        checkers.untar(self.env.get_admin_remote(),
                       os.path.basename(hlp_data.
                                        UPGRADE_TARBALL_PATH), '/var')
        self.fuel_web.modify_python_file(self.env.get_admin_remote(),
                                         "83i \ \ \ \ \ \ \ \ raise errors."
                                         "ExecutedErrorNonZeroExitCode('{0}')"
                                         .format('Some bad error'),
                                         '/var/upgrade/site-packages/'
                                         'fuel_upgrade/engines/'
                                         'docker_engine.py')
        checkers.run_with_rollback(self.env.get_admin_remote(),
                                   '/var', 'upgrade.sh')
        checkers.wait_rollback_is_done(self.env.get_admin_remote(), 1800)
        checkers.check_upgraded_containers(self.env.get_admin_remote(),
                                           hlp_data.UPGRADE_FUEL_TO,
                                           hlp_data.UPGRADE_FUEL_FROM)
        self.fuel_web.wait_nodes_get_online_state(self.env.nodes().slaves[:3])
        self.fuel_web.assert_nodes_in_ready_state(cluster_id)
        self.fuel_web.assert_fuel_version(hlp_data.UPGRADE_FUEL_FROM)
        self.fuel_web.run_ostf(
            cluster_id=cluster_id,
            should_fail=1,
            failed_test_name=['Create volume and attach it to instance'])
        self.env.bootstrap_nodes(self.env.nodes().slaves[3:4])
        self.fuel_web.update_nodes(
            cluster_id, {'slave-04': ['cinder']},
            True, False
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)
        self.fuel_web.run_ostf(cluster_id=cluster_id)

        self.env.make_snapshot("rollback_automatic")
