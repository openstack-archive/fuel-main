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
from proboscis.asserts import assert_true
from proboscis import test

from fuelweb_test.helpers.decorators import log_snapshot_on_error
from fuelweb_test.helpers import checkers
from fuelweb_test.settings import DEPLOYMENT_MODE
from fuelweb_test.settings import GLUSTER_CLUSTER_ENDPOINT
from fuelweb_test.settings import GLUSTER_PLUGIN_PATH
from fuelweb_test.settings import NEUTRON_ENABLE
from fuelweb_test.settings import NEUTRON_SEGMENT_TYPE
from fuelweb_test.tests.base_test_case import SetupEnvironment
from fuelweb_test.tests.base_test_case import TestBasic


@test(groups=["plugins"])
class GlusterfsPlugin(TestBasic):
    @classmethod
    def check_glusterfs_conf(cls, remote, path, gfs_endpoint):
        cmd = ' cat {0}'.format(path)
        result = remote.execute(cmd)
        assert_equal(result['exit_code'],
                     0,
                     'Command {0} execution failed with non-zero exit code. '
                     'Actual result {1} stderr {2}'.format(
                         cmd, result['exit_code'], result['stderr']))
        assert_true(gfs_endpoint in ''.join(result['stdout']),
                    'Can not find gsf endpoint in gfs configs')

    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["deploy_ha_one_controller_glusterfs"])
    @log_snapshot_on_error
    def deploy_ha_one_controller_glusterfs_simple(self):
        """Deploy cluster in ha mode with glusterfs plugin

        Scenario:
            1. Upload plugin to the master node
            2. Install plugin
            3. Create cluster
            4. Add 1 node with controller and cinder roles
            5. Add 1 nodes with compute role
            6. Add 1 nodes with cinder role
            7. Deploy the cluster
            8. Run network verification
            9. Check plugin health
            10. Run OSTF

        Duration 35m
        Snapshot deploy_ha_one_controller_glusterfs
        """
        self.env.revert_snapshot("ready_with_3_slaves")

        # copy plugin to the master node

        checkers.upload_tarball(
            self.env.get_admin_remote(), GLUSTER_PLUGIN_PATH, '/var')

        # install plugin

        checkers.install_plugin_check_code(
            self.env.get_admin_remote(),
            plugin=os.path.basename(GLUSTER_PLUGIN_PATH))

        settings = None

        if NEUTRON_ENABLE:
            settings = {
                "net_provider": 'neutron',
                "net_segment_type": NEUTRON_SEGMENT_TYPE
            }

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE,
            settings=settings
        )

        attr = self.fuel_web.client.get_cluster_attributes(cluster_id)
        if 'external_glusterfs' in attr['editable']:
            plugin_enabled = attr['editable']['external_glusterfs']['metadata']
            plugin_enabled['enabled'] = True
            plugin_data = attr['editable']['external_glusterfs']['endpoint']
            plugin_data['value'] = GLUSTER_CLUSTER_ENDPOINT

        self.fuel_web.client.update_cluster_attributes(cluster_id, attr)

        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller', 'cinder'],
                'slave-02': ['compute'],
                'slave-03': ['cinder']
            }
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)

        for node in ('slave-01', 'slave-03'):
            self.check_glusterfs_conf(
                remote=self.env.get_ssh_to_remote_by_name(node),
                path='/etc/cinder/glusterfs',
                gfs_endpoint=GLUSTER_CLUSTER_ENDPOINT)

        self.fuel_web.verify_network(cluster_id)

        self.fuel_web.run_ostf(
            cluster_id=cluster_id)

        self.env.make_snapshot("deploy_ha_one_controller_glusterfs")

    @test(depends_on=[SetupEnvironment.prepare_slaves_5],
          groups=["deploy_glusterfs_ha"])
    @log_snapshot_on_error
    def deploy_glusterfs_ha(self):
        """Deploy cluster in ha mode with glusterfs plugin

        Scenario:
            1. Upload plugin to the master node
            2. Install plugin
            3. Create cluster
            4. Add 1 node with controller and cinder roles
            5. Add 1 nodes with compute role
            6. Add 1 nodes with cinder role
            7. Deploy the cluster
            8. Run network verification
            9. Check plugin health
            10. Run OSTF
            11. Add 2 cinder + controller nodes
            12. Re-deploy cluster
            13. Check plugin health
            14. Run ostf

        Duration 50m
        Snapshot deploy_glasterfs_ha

        """
        self.env.revert_snapshot("ready_with_5_slaves")

        # copy plugin to the master node

        checkers.upload_tarball(
            self.env.get_admin_remote(), GLUSTER_PLUGIN_PATH, '/var')

        # install plugin

        checkers.install_plugin_check_code(
            self.env.get_admin_remote(),
            plugin=os.path.basename(GLUSTER_PLUGIN_PATH))

        settings = None

        if NEUTRON_ENABLE:
            settings = {
                "net_provider": 'neutron',
                "net_segment_type": NEUTRON_SEGMENT_TYPE
            }

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE,
            settings=settings
        )

        attr = self.fuel_web.client.get_cluster_attributes(cluster_id)
        if 'external_glusterfs' in attr['editable']:
            plugin_enabled = attr['editable']['external_glusterfs']['metadata']
            plugin_enabled['enabled'] = True
            plugin_data = attr['editable']['external_glusterfs']['endpoint']
            plugin_data['value'] = GLUSTER_CLUSTER_ENDPOINT

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

        self.check_glusterfs_conf(
            remote=self.env.get_ssh_to_remote_by_name('slave-03'),
            path='/etc/cinder/glusterfs',
            gfs_endpoint=GLUSTER_CLUSTER_ENDPOINT)

        self.fuel_web.verify_network(cluster_id)

        self.fuel_web.run_ostf(
            cluster_id=cluster_id)

        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-04': ['controller, cinder'],
                'slave-05': ['controller, cinder'],
            }
        )

        self.fuel_web.deploy_cluster_wait(cluster_id)

        for node in ('slave-03', 'slave-04', 'slave-05'):
            self.check_glusterfs_conf(
                remote=self.env.get_ssh_to_remote_by_name(node),
                path='/etc/cinder/glusterfs',
                gfs_endpoint=GLUSTER_CLUSTER_ENDPOINT)

        self.fuel_web.run_ostf(
            cluster_id=cluster_id)

        self.env.make_snapshot("deploy_glusterfs_ha")
