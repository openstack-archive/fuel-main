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
import urllib
import hashlib
import os.path

from devops.helpers.helpers import SSHClient
from proboscis import test
from fuelweb_test.helpers.checkers \
    import verify_savanna_service, verify_murano_service
from fuelweb_test.helpers.decorators import debug, log_snapshot_on_error
from fuelweb_test.tests.base_test_case import TestBasic, SetupEnvironment

logger = logging.getLogger(__name__)
logwrap = debug(logger)


@test(groups=["thread_1", "services", "services.savanna"])
class SavannaSimple(TestBasic):

    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["deploy_savanna_simple"])
    @log_snapshot_on_error
    def deploy_savanna_simple(self):
        """Deploy cluster in simple mode with Savanna

        Scenario:
            1. Create cluster. Set install Savanna option
            2. Add 1 node with controller role
            3. Add 1 nodes with compute role
            4. Deploy the cluster
            5. Verify savanna services


        Snapshot: deploy_savanna_simple

        """
        self.env.revert_snapshot("ready_with_3_slaves")

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            settings={
                'savanna': True
            }
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['compute']
            }
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)
        self.fuel_web.assert_cluster_ready(
            'slave-01', smiles_count=6, networks_count=1, timeout=500)
        verify_savanna_service(self.env.get_ssh_to_remote_by_name("slave-01"))
        self.env.make_snapshot("deploy_savanna_simple")

    @test(depends_on=[deploy_savanna_simple],
          groups=["deploy_savanna_simple_ostf"])
    @log_snapshot_on_error
    def deploy_savanna_simple_ostf(self):
        """Run OSTF tests on cluster in simple mode with Savanna

        Scenario:
            1. Revert snapshot "deploy_savanna_simple"
            2. Run OSTF
            3. Register savanna image
            4. Run OSTF platform tests

        """
        self.env.revert_snapshot("deploy_savanna_simple")

        self.fuel_web.run_ostf(
            cluster_id=self.fuel_web.get_last_created_cluster(),
            should_fail=6, should_pass=18
        )

        server_url = "http://savanna-files.mirantis.com"
        savanna_image = "savanna-0.3-vanilla-1.2.1-ubuntu-13.04.qcow2"
        savanna_url = "%s/%s" % (server_url, savanna_image)
        savanna_local_path = "/tmp/%s" % savanna_image
        savanna_md5 = '9ab37ec9a13bb005639331c4275a308d'

        if not os.path.isfile(savanna_local_path):
            urllib.urlretrieve(savanna_url, savanna_local_path)
        if (hashlib.md5(open(savanna_local_path).read()).hexdigest()
                != savanna_md5):
            urllib.urlretrieve(savanna_url, savanna_local_path)

        logger.debug('Copy savanna iso to slave-01')
        remote = self.env.get_ssh_to_remote_by_name('slave-01')
        remote.upload(savanna_local_path, savanna_local_path)
        remote.execute('. /root/openrc; glance image-create --name savanna '
                       '--disk-format qcow2 --file %s '
                       '--container-format bare' % savanna_local_path)['stdout']
        remote.execute(". /root/openrc; nova image-meta savanna set "
                       "'_savanna_tag_1.2.1'=True  "
                       "'_savanna_tag_vanilla'=True "
                       "'_savanna_username'='ubuntu'")

        logger.debug('Run OSTF platform tests')

        self.fuel_web.run_ostf(cluster_id=self.fuel_web.get_last_created_cluster(),
                               test_sets='platform_tests', should_fail=0, should_pass=1)


@test(groups=["thread_1", "services", "services.murano"])
class MuranoSimple(TestBasic):

    @test(depends_on=[SetupEnvironment.prepare_slaves_5],
          groups=["deploy_murano_simple"])
    @log_snapshot_on_error
    def deploy_murano_simple(self):
        """Deploy cluster in simple mode with Murano

        Scenario:
            1. Create cluster. Set install Murano option
            2. Add 1 node with controller role
            3. Add 3 nodes with compute role
            4. Add 1 node with cinder role
            4. Deploy the cluster
            5. Verify murano services

        Snapshot: deploy_murano_simple

        """
        self.env.revert_snapshot("ready_with_5_slaves")

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            settings={
                'murano': True
            }
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['compute'],
                'slave-03': ['compute'],
                'slave-04': ['compute'],
                'slave-05': ['cinder']
            }
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)
        self.fuel_web.assert_cluster_ready(
            'slave-01', smiles_count=10, networks_count=1, timeout=500)
        verify_murano_service(self.env.get_ssh_to_remote_by_name("slave-01"))
        self.env.make_snapshot("deploy_murano_simple")

    @test(depends_on=[deploy_murano_simple],
          groups=["deploy_murano_simple_ostf"])
    @log_snapshot_on_error
    def deploy_murano_simple_ostf(self):
        """Run OSTF tests on cluster in simple mode with Murano

        Scenario:
            1. Revert snapshot "deploy_murano_simple"
            2. Run OSTF

        """
        self.env.revert_snapshot("deploy_murano_simple")

        self.fuel_web.run_ostf(
            cluster_id=self.fuel_web.get_last_created_cluster(),
            should_fail=5, should_pass=19
        )
