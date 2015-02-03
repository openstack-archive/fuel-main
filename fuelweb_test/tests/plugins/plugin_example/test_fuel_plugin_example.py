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

from fuelweb_test import logger
from fuelweb_test.helpers.decorators import log_snapshot_on_error
from fuelweb_test.helpers import checkers
from fuelweb_test.settings import DEPLOYMENT_MODE
from fuelweb_test.settings import EXAMPLE_PLUGIN_PATH
from fuelweb_test.tests.base_test_case import SetupEnvironment
from fuelweb_test.tests.base_test_case import TestBasic


@test(groups=["plugins"])
class ExamplePlugin(TestBasic):

    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["deploy_ha_controller_neutron_example"])
    @log_snapshot_on_error
    def deploy_ha_one_controller_neutron_example(self):
        """Deploy cluster in ha mode with example plugin

        Scenario:
            1. Upload plugin to the master node
            2. Install plugin
            3. Create cluster
            4. Add 1 node with controller role
            5. Add 2 nodes with compute role
            6. Deploy the cluster
            7. Run network verification
            8. Check plugin health
            9. Run OSTF

        Duration 35m
        Snapshot deploy_ha_one_controller_neutron_example
        """
        self.env.revert_snapshot("ready_with_3_slaves")

        # copy plugin to the master node

        checkers.upload_tarball(
            self.env.get_admin_remote(),
            EXAMPLE_PLUGIN_PATH, '/var')

        # install plugin

        checkers.install_plugin_check_code(
            self.env.get_admin_remote(),
            plugin=os.path.basename(EXAMPLE_PLUGIN_PATH))

        segment_type = 'vlan'
        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE,
            settings={
                "net_provider": 'neutron',
                "net_segment_type": segment_type,
            }
        )

        attr = self.fuel_web.client.get_cluster_attributes(cluster_id)
        if 'fuel_plugin_example' in attr['editable']:
            plugin_data = attr['editable']['fuel_plugin_example']['metadata']
            plugin_data['enabled'] = True

        self.fuel_web.client.update_cluster_attributes(cluster_id, attr)

        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['compute'],
                'slave-03': ['compute']
            }
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)

        self.fuel_web.verify_network(cluster_id)

        # check if service ran on controller
        logger.debug("Start to check service on node {0}".format('slave-01'))
        cmd_curl = 'curl localhost:8234'
        cmd = 'pgrep -f fuel-simple-service'
        res_pgrep = self.env.get_ssh_to_remote_by_name(
            'slave-01').execute(cmd)
        assert_equal(0, res_pgrep['exit_code'],
                     'Failed with error {0}'.format(res_pgrep['stderr']))
        assert_equal(1, len(res_pgrep['stdout']),
                     'Failed with error {0}'.format(res_pgrep['stderr']))
        # curl to service
        res_curl = self.env.get_ssh_to_remote_by_name(
            'slave-01').execute(cmd_curl)
        assert_equal(0, res_pgrep['exit_code'],
                     'Failed with error {0}'.format(res_curl['stderr']))

        self.fuel_web.run_ostf(
            cluster_id=cluster_id)

        self.env.make_snapshot("deploy_ha_one_controller_neutron_example")

    @test(depends_on=[SetupEnvironment.prepare_slaves_5],
          groups=["deploy_nova_example_ha"])
    @log_snapshot_on_error
    def deploy_nova_example_ha(self):
        """Deploy cluster in ha mode with example plugin

        Scenario:
            1. Upload plugin to the master node
            2. Install plugin
            3. Create cluster
            4. Add 3 node with controller role
            5. Add 1 nodes with compute role
            6. Add 1 nodes with cinder role
            7. Deploy the cluster
            8. Run network verification
            9. check plugin health
            10. Run OSTF

        Duration 70m
        Snapshot deploy_nova_example_ha

        """
        self.env.revert_snapshot("ready_with_5_slaves")

        # copy plugin to the master node

        checkers.upload_tarball(
            self.env.get_admin_remote(), EXAMPLE_PLUGIN_PATH, '/var')

        # install plugin

        checkers.install_plugin_check_code(
            self.env.get_admin_remote(),
            plugin=os.path.basename(EXAMPLE_PLUGIN_PATH))

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE,
        )

        attr = self.fuel_web.client.get_cluster_attributes(cluster_id)
        if 'fuel_plugin_example' in attr['editable']:
            plugin_data = attr['editable']['fuel_plugin_example']['metadata']
            plugin_data['enabled'] = True

        self.fuel_web.client.update_cluster_attributes(cluster_id, attr)

        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['controller'],
                'slave-03': ['controller'],
                'slave-04': ['compute'],
                'slave-05': ['cinder']
            }
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)
        self.fuel_web.verify_network(cluster_id)

        for node in ('slave-01', 'slave-02', 'slave-03'):
            logger.debug("Start to check service on node {0}".format(node))
            cmd_curl = 'curl localhost:8234'
            cmd = 'pgrep -f fuel-simple-service'
            res_pgrep = self.env.get_ssh_to_remote_by_name(
                node).execute(cmd)
            assert_equal(0, res_pgrep['exit_code'],
                         'Failed with error {0} '
                         'on node {1}'.format(res_pgrep['stderr'], node))
            assert_equal(1, len(res_pgrep['stdout']),
                         'Failed with error {0} on the '
                         'node {1}'.format(res_pgrep['stderr'], node))
            # curl to service
            res_curl = self.env.get_ssh_to_remote_by_name(
                node).execute(cmd_curl)
            assert_equal(0, res_pgrep['exit_code'],
                         'Failed with error {0} '
                         'on node {1}'.format(res_curl['stderr'], node))

        self.fuel_web.run_ostf(
            cluster_id=cluster_id)

        self.env.make_snapshot("deploy_nova_example_ha")

    @test(depends_on=[SetupEnvironment.prepare_slaves_5],
          groups=["deploy_neutron_example_ha_add_node"])
    @log_snapshot_on_error
    def deploy_neutron_example_ha_add_node(self):
        """Deploy and scale cluster in ha mode with example plugin

        Scenario:
            1. Upload plugin to the master node
            2. Install plugin
            3. Create cluster
            4. Add 1 node with controller role
            5. Add 1 nodes with compute role
            6. Add 1 nodes with cinder role
            7. Deploy the cluster
            8. Run network verification
            9. Check plugin health
            10 Add 2 nodes with controller role
            11. Deploy cluster
            12. Check plugin health
            13. Run OSTF

        Duration 150m
        Snapshot deploy_neutron_example_ha_add_node

        """
        self.env.revert_snapshot("ready_with_5_slaves")

        # copy plugin to the master node

        checkers.upload_tarball(
            self.env.get_admin_remote(), EXAMPLE_PLUGIN_PATH, '/var')

        # install plugin

        checkers.install_plugin_check_code(
            self.env.get_admin_remote(),
            plugin=os.path.basename(EXAMPLE_PLUGIN_PATH))

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE,
            settings={
                "net_provider": 'neutron',
                "net_segment_type": 'gre',
            }
        )

        attr = self.fuel_web.client.get_cluster_attributes(cluster_id)
        if 'fuel_plugin_example' in attr['editable']:
            plugin_data = attr['editable']['fuel_plugin_example']['metadata']
            plugin_data['enabled'] = True

        self.fuel_web.client.update_cluster_attributes(cluster_id, attr)

        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['compute'],
                'slave-03': ['cinder']
            }
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)
        self.fuel_web.verify_network(cluster_id)

         # check if service ran on controller
        logger.debug("Start to check service on node {0}".format('slave-01'))
        cmd_curl = 'curl localhost:8234'
        cmd = 'pgrep -f fuel-simple-service'
        res_pgrep = self.env.get_ssh_to_remote_by_name(
            'slave-01').execute(cmd)
        assert_equal(0, res_pgrep['exit_code'],
                     'Failed with error {0}'.format(res_pgrep['stderr']))
        assert_equal(1, len(res_pgrep['stdout']),
                     'Failed with error {0}'.format(res_pgrep['stderr']))
        # curl to service
        res_curl = self.env.get_ssh_to_remote_by_name(
            'slave-01').execute(cmd_curl)
        assert_equal(0, res_pgrep['exit_code'],
                     'Failed with error {0}'.format(res_curl['stderr']))

        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-04': ['controller'],
                'slave-05': ['controller'],
            }
        )

        self.fuel_web.deploy_cluster_wait(cluster_id)

        for node in ('slave-01', 'slave-04', 'slave-05'):
            logger.debug("Start to check service on node {0}".format(node))
            cmd_curl = 'curl localhost:8234'
            cmd = 'pgrep -f fuel-simple-service'
            res_pgrep = self.env.get_ssh_to_remote_by_name(
                node).execute(cmd)
            assert_equal(0, res_pgrep['exit_code'],
                         'Failed with error {0} '
                         'on node {1}'.format(res_pgrep['stderr'], node))
            assert_equal(1, len(res_pgrep['stdout']),
                         'Failed with error {0} on the '
                         'node {1}'.format(res_pgrep['stderr'], node))
            # curl to service
            res_curl = self.env.get_ssh_to_remote_by_name(
                node).execute(cmd_curl)
            assert_equal(0, res_pgrep['exit_code'],
                         'Failed with error {0} '
                         'on node {1}'.format(res_curl['stderr'], node))

        # add verification here
        self.fuel_web.run_ostf(
            cluster_id=cluster_id)

        self.env.make_snapshot("deploy_neutron_example_ha_add_node")
