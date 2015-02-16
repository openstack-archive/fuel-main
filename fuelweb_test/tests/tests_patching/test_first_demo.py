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
import traceback

from proboscis.asserts import assert_equal
from proboscis import SkipTest
from proboscis import test

from fuelweb_test import logger
from fuelweb_test.settings import CUSTOM_PKGS_MIRROR
from fuelweb_test.settings import OPENSTACK_RELEASE
from fuelweb_test.settings import OPENSTACK_RELEASE_UBUNTU
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
        if not self.env.revert_snapshot(snapshot_name):
            logger.error('Environment revert from snapshot "{0}" failed.'.
                         format(snapshot_name))
            raise SkipTest()

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

        bug_id = os.environ.get("BUG_ID", "")

        tests_parent_dir = ('{0}/patching_tests/bug{1}/tests'.
                            format(os.environ.get("WORKSPACE", "./"),
                                   bug_id))

        tests_dir_on_master = "/tmp/tests{0}".format(bug_id)
        repo_script = "patch-from-repo.sh"

        admin.upload('{0}/{1}'.format(parent_dir, repo_script), "/var/")
        try:
            admin.upload('{0}'.format(tests_parent_dir), tests_dir_on_master)
        except Exception:
            logger.error('Uploading folder {0} on master node failed.'.format(
                tests_parent_dir))
            logger.error(traceback.format_exc())

        repo_script_admin = os.path.join("/var", repo_script)
        admin.execute('chmod 755 {0}'.format(repo_script_admin))
        repo_link = CUSTOM_PKGS_MIRROR
        cluster_id = self.fuel_web.get_last_created_cluster()

        cmd_res = admin.execute("{0} {1} {2}".format(repo_script_admin,
                                                     repo_link,
                                                     cluster_id))
        logger.debug("Installation of patched packages on nodes was completed")

        assert_equal(0, cmd_res['exit_code'], "Command failed with error: {0}".
                     format(cmd_res))

        # Shutdown all nodes in cluster; start Controller node, wait until in
        # became online; start other nodes in cluster.
        controller_nodes = self.env.devops_nodes_by_names(['slave-01'])
        other_nodes = self.env.devops_nodes_by_names(['slave-02', 'slave-03'])
        self.fuel_web.warm_shutdown_nodes(self.env.nodes().slaves[:3])
        self.fuel_web.warm_start_nodes(controller_nodes)
        self.fuel_web.warm_start_nodes(other_nodes)

        # Manually start cinder-volume on slaves if Ubuntu is used (LP#1421595)
        if OPENSTACK_RELEASE == OPENSTACK_RELEASE_UBUNTU:
            for node in other_nodes:
                slave_remote = self.env.get_ssh_to_remote_by_name(node.name)
                self.env.execute_remote_cmd(remote=slave_remote,
                                            cmd='service cinder-volume start')
        self.fuel_web.wait_cinder_is_up(['slave-01'])

        self.fuel_web.run_ostf(cluster_id=cluster_id, test_sets=['smoke',
                                                                 'sanity'])
        tests = []
        try:
            tests = os.listdir(tests_parent_dir)
        except Exception:
            logger.error('Discovering tests in  folder "{0}" failed.'.format(
                tests_parent_dir))
            logger.error(traceback.format_exc())
        for filename in tests:
            result = admin.execute("cd {0}; chmod +x {1} && ./{1}".
                                   format(tests_dir_on_master, filename))
            assert_equal(0, result['exit_code'],
                         "Command failed with error: {0}".format(result))
