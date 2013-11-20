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
from devops.helpers.helpers import SSHClient

from proboscis import test, SkipTest

from fuelweb_test.models.environment import EnvironmentModel
from fuelweb_test.helpers.decorators import debug
from fuelweb_test.settings import *

logging.basicConfig(
    format='%(asctime)s - %(levelname)s %(filename)s:'
           '%(lineno)d -- %(message)s',
    level=logging.DEBUG
)

logger = logging.getLogger(__name__)
logwrap = debug(logger)


class TestBasic(object):
    """Basic test case class for all system tests.

    Initializes EnvironmentModel and FuelWebModel.

    """
    def __init__(self):
        self.env = EnvironmentModel()
        self.fuel_web = self.env.fuel_web

    def check_run(self, snapshot_name):
        """Checks if run of current test is required.

        :param snapshot_name: Name of the snapshot the function should make
        :type snapshot_name: str
        :raises: SkipTest

        """
        if snapshot_name != "" and snapshot_name is not None:
            if self.env.get_virtual_environment().has_snapshot(snapshot_name):
                raise SkipTest()


@test
class SetupEnvironment(TestBasic):
    @test(groups=["setup"])
    def setup_master(self):
        """Create environment and set up master node

        Snapshot: empty

        """
        self.check_run("empty")
        self.env.setup_environment()
        self.env.make_snapshot("empty")

    @test(depends_on=[setup_master])
    def prepare_release(self):
        """Prepare master node

        Scenario:
            1. Revert snapshot "empty"
            2. Download the release if needed. Uploads custom manifest.

        Snapshot: ready

        """
        self.check_run("ready")
        self.env.revert_snapshot("empty")

        if OPENSTACK_RELEASE == OPENSTACK_RELEASE_REDHAT:
            self.fuel_web.update_redhat_credentials()
            self.fuel_web.assert_release_state(
                OPENSTACK_RELEASE_REDHAT,
                state='available'
            )

        try:
            if UPLOAD_MANIFESTS:
                logging.info("Uploading new manifests from %s" %
                             UPLOAD_MANIFESTS_PATH)
                remote = SSHClient(self.env.get_admin_node_ip(),
                                   username='root',
                                   password='r00tme')
                remote.execute('rm -rf /etc/puppet/modules/*')
                remote.upload(UPLOAD_MANIFESTS_PATH, '/etc/puppet/modules/')
                logging.info("Copying new site.pp from %s" %
                             SITEPP_FOR_UPLOAD)
                remote.execute("cp %s /etc/puppet/manifests" %
                               SITEPP_FOR_UPLOAD)
        except:
            logging.error("Could not upload manifests")
            raise
        self.env.make_snapshot("ready")

    @test(depends_on=[prepare_release])
    def prepare_slaves_3(self):
        """Bootstrap 3 slave nodes

        Scenario:
            1. Revert snapshot "ready"
            2. Start 3 slave nodes

        Snapshot: ready_with_3_slaves

        """
        self.check_run("ready_with_3_slaves")
        self.env.revert_snapshot("ready")
        self.env.bootstrap_nodes(self.env.nodes().slaves[:3])
        self.env.make_snapshot("ready_with_3_slaves")

    @test(depends_on=[prepare_release])
    def prepare_slaves_5(self):
        """Bootstrap 5 slave nodes

        Scenario:
            1. Revert snapshot "ready"
            2. Start 5 slave nodes

        Snapshot: ready_with_5_slaves

        """
        self.check_run("ready_with_5_slaves")
        self.env.revert_snapshot("ready")
        self.env.bootstrap_nodes(self.env.nodes().slaves[:5])
        self.env.make_snapshot("ready_with_5_slaves")
