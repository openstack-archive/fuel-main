#    Copyright 2015 Mirantis, Inc.
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

from fuelweb_test.settings import CUSTOM_PKGS_MIRROR
from fuelweb_test.helpers.decorators import log_snapshot_on_error
from fuelweb_test.helpers.fuel_actions import FuelActions
from fuelweb_test.tests.base_test_case import TestBasic


@test(groups=["first_patching_demo"])
class TestPatching(TestBasic):
    @test(groups=["first_patching_demo"])
    @log_snapshot_on_error
    def first_patching_demo(self):
        """
        """
        snapshot_name = "deploy_neutron_gre"
        assert_true(self.env.revert_snapshot(snapshot_name),
                    'Environment revert from snapshot "{0}" failed.'.format(
                        snapshot_name))

        admin = self.env.get_admin_remote()
        router_ip = self.env.router()
        fuel_actions = FuelActions.BaseActions(admin_remote=admin)

        fuel_actions.execute_in_container(
            command="sed '$anameserver {0}' -i /etc/dnsmasq.upstream".format(
                router_ip),
            container='cobbler',
            exit_code=0,
        )
        fuel_actions.execute_in_container(
            command='service dnsmasq reload',
            container='cobbler',
            exit_code=0
        )

        required_packages = ['yum-utils', 'dpkg', 'dpkg-devel', 'createrepo']
        for package in required_packages:
            assert_equal(self.env.admin_install_pkg(package), 0,
                         "Installation of '{0}' package on master node failed".
                         format(package))

        parent_dir = ('{0}/fuelweb_test/helpers/'
                      .format(os.environ.get("WORKSPACE", "./")))

        repo_script = "patch-from-repo.sh"

        admin.upload('{0}/{1}'.format(parent_dir, repo_script), "/var/")

        repo_script_admin = os.path.join("/var", repo_script)
        admin.execute('chmod 755 {0}'.format(repo_script_admin))
        repo_link = CUSTOM_PKGS_MIRROR
        cluster_id = self.fuel_web.get_last_created_cluster()

        cmd_res = admin.execute("{0} {1} {2}".format(repo_script_admin,
                                                     repo_link,
                                                     cluster_id))

        assert_equal(0, cmd_res['exit_code'], "Command failed with error: {0}".
                     format(cmd_res))

        self.fuel_web.warm_restart_nodes(self.env.nodes().slaves[:3])

        self.fuel_web.wait_cinder_is_up(['slave-01'])

        self.fuel_web.run_ostf(cluster_id=cluster_id, test_sets=['smoke',
                                                                 'sanity'])
