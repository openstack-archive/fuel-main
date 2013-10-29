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
import xmlrpclib
from devops.helpers.helpers import wait, tcp_ping, http

from proboscis import test, SkipTest
from proboscis.asserts import assert_equal

from fuelweb_test.helpers.decorators import debug, log_snapshot_on_error
from fuelweb_test.settings import OPENSTACK_RELEASE, OPENSTACK_RELEASE_CENTOS
from fuelweb_test.tests.base_test_case import SetupEnvironment, TestBasic

logger = logging.getLogger(__name__)
logwrap = debug(logger)


@test
class TestAdminNode(TestBasic):

    @test(groups=["thread_1"], depends_on=[SetupEnvironment.setup_master])
    def test_puppet_master_alive(self):
        if OPENSTACK_RELEASE != OPENSTACK_RELEASE_CENTOS:
            raise SkipTest()
        self.env.revert_snapshot("empty")
        wait(
            lambda: tcp_ping(self.env.get_admin_node_ip(), 8140),
            timeout=5
        )
        ps_output = self.env.get_admin_remote().execute('ps ax')['stdout']
        pm_processes = filter(
            lambda x: '/usr/sbin/puppetmasterd' in x,
            ps_output
        )
        logging.debug("Found puppet master processes: %s" % pm_processes)
        assert_equal(len(pm_processes), 4)

    @test(groups=["thread_1"], depends_on=[SetupEnvironment.setup_master])
    def test_cobbler_alive(self):
        if OPENSTACK_RELEASE != OPENSTACK_RELEASE_CENTOS:
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

    @log_snapshot_on_error
    @test(groups=["thread_1"], depends_on=[SetupEnvironment.setup_master])
    def test_nailyd_alive(self):
        if OPENSTACK_RELEASE != OPENSTACK_RELEASE_CENTOS:
            raise SkipTest()
        self.env.revert_snapshot("empty")
        ps_output = self.env.get_admin_remote().execute('ps ax')['stdout']
        naily_master = filter(lambda x: 'naily master' in x, ps_output)
        logging.debug("Found naily processes: %s" % naily_master)
        assert_equal(len(naily_master), 1)
        naily_workers = filter(lambda x: 'naily worker' in x, ps_output)
        logging.debug(
            "Found %d naily worker processes: %s" %
            (len(naily_workers), naily_workers))
        assert_equal(True, len(naily_workers) > 1)
