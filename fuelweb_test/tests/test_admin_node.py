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


from devops.helpers.helpers import http
from devops.helpers.helpers import wait
from proboscis.asserts import assert_equal
from proboscis import SkipTest
from proboscis import test
import xmlrpclib

from fuelweb_test.helpers.decorators import log_snapshot_on_error
from fuelweb_test.settings import OPENSTACK_RELEASE
from fuelweb_test.settings import OPENSTACK_RELEASE_CENTOS
from fuelweb_test.tests.base_test_case import SetupEnvironment
from fuelweb_test.tests.base_test_case import TestBasic
from fuelweb_test import logger


@test(groups=["thread_1"])
class TestAdminNode(TestBasic):
    @test(depends_on=[SetupEnvironment.setup_master])
    def test_cobbler_alive(self):
        """Test current installation has correctly setup cobbler

        API and cobbler HTTP server are alive

        Scenario:
            1. Revert snapshot "empty"
            2. test cobbler API and HTTP server through send http request

        """
        if OPENSTACK_RELEASE_CENTOS not in OPENSTACK_RELEASE:
            raise SkipTest()
        self.env.revert_snapshot("empty")
        wait(
            lambda: http(host=self.env.get_admin_node_ip(), url='/cobbler_api',
                         waited_code=502),
            timeout=60
        )
        server = xmlrpclib.Server(
            'http://%s/cobbler_api' % self.env.get_admin_node_ip())
        # raises an error if something isn't right
        server.login('cobbler', 'cobbler')

    @test(depends_on=[SetupEnvironment.setup_master])
    @log_snapshot_on_error
    def test_astuted_alive(self):
        """Test astute master and worker processes are alive on master node

        Scenario:
            1. Revert snapshot "empty"
            2. Search for master and child processes

        """
        if OPENSTACK_RELEASE_CENTOS not in OPENSTACK_RELEASE:
            raise SkipTest()
        self.env.revert_snapshot("empty")
        ps_output = self.env.get_admin_remote().execute('ps ax')['stdout']
        astute_master = filter(lambda x: 'astute master' in x, ps_output)
        logger.info("Found astute processes: %s" % astute_master)
        assert_equal(len(astute_master), 1)
        astute_workers = filter(lambda x: 'astute worker' in x, ps_output)
        logger.info(
            "Found %d astute worker processes: %s" %
            (len(astute_workers), astute_workers))
        assert_equal(True, len(astute_workers) > 1)
