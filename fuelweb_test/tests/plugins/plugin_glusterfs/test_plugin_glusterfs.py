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

from fuelweb_test.helpers.decorators import log_snapshot_on_error
from fuelweb_test.helpers import os_actions
from fuelweb_test.helpers import checkers
from fuelweb_test.settings import DEPLOYMENT_MODE_HA
from fuelweb_test.settings import DEPLOYMENT_MODE_SIMPLE
from fuelweb_test.settings import PLUGIN_PATH
from fuelweb_test.tests.base_test_case import SetupEnvironment
from fuelweb_test.tests.base_test_case import TestBasic
from fuelweb_test import logger

@test(groups=["plugins"])
class GlusterfsPlugin(TestBasic):

    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["deploy_neutron_glusterfs_simple"])
    @log_snapshot_on_error
    def deploy_neutron_glusterfs_simple(self):
        """Deploy cluster in simple mode with glusterfs plugin

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
            10. Run OSTF

        Snapshot deploy_neutron_example_simple

        """
        self.env.revert_snapshot("ready_with_3_slaves")

        # copy plugin to the master node

        checkers.upload_tarball(
            self.env.get_admin_remote(), PLUGIN_PATH, '/var')

        # install plugin

        checkers.install_plugin_check_code(
            self.env.get_admin_remote(),
            plugin=os.path.basename(PLUGIN_PATH))

        segment_type = 'vlan'
        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE_SIMPLE,
            settings={
                "net_provider": 'neutron',
                "net_segment_type": segment_type,
            }
        )

        attr = self.fuel_web.client.get_cluster_attributes(cluster_id)
        if 'glusterfs' in attr['editable']:
            plugin_data = attr['editable']['glusterfs']['metadata']
            plugin_data['enabled'] = True
            # TODO tleontovich: add here glusterfs property

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
        # TODO tleontovich: Check that conf is updated, packages installed and if possible storage placed in glusterfs

        cluster = self.fuel_web.client.get_cluster(cluster_id)
        assert_equal(str(cluster['net_provider']), 'neutron')

        self.fuel_web.verify_network(cluster_id)

        controller = self.fuel_web.get_nailgun_node_by_name('slave-01')
        # add verification here
        self.fuel_web.run_ostf(
            cluster_id=cluster_id)

        self.env.make_snapshot("deploy_neutron_glusterfs_simple", is_make=True)
