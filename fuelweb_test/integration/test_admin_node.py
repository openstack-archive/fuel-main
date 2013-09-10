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
import unittest
import xmlrpclib
from devops.helpers.helpers import wait, tcp_ping, http
from fuelweb_test.integration.base_test_case import BaseTestCase
from fuelweb_test.integration.decorators import debug, fetch_logs
from fuelweb_test.settings import CLEAN

logger = logging.getLogger(__name__)
logwrap = debug(logger)


class TestAdminNode(BaseTestCase):
    def setUp(self):
        if CLEAN:
            self.get_empty_environment()

    @logwrap
    def test_puppetmaster_alive(self):
        wait(
            lambda: tcp_ping(self.get_admin_node_ip(), 8140),
            timeout=5
        )
        ps_output = self.remote().execute('ps ax')['stdout']
        pm_processes = filter(
            lambda x: '/usr/sbin/puppetmasterd' in x,
            ps_output
        )
        logging.debug("Found puppet master processes: %s" % pm_processes)
        self.assertEquals(len(pm_processes), 4)

    @logwrap
    def test_cobbler_alive(self):
        wait(
            lambda: http(host=self.get_admin_node_ip(), url='/cobbler_api',
                         waited_code=502),
            timeout=60
        )
        server = xmlrpclib.Server(
            'http://%s/cobbler_api' % self.get_admin_node_ip())
        # raises an error if something isn't right
        server.login('cobbler', 'cobbler')

    @logwrap
    @fetch_logs
    def test_nailyd_alive(self):
        ps_output = self.remote().execute('ps ax')['stdout']
        naily_master = filter(lambda x: 'naily master' in x, ps_output)
        logging.debug("Found naily processes: %s" % naily_master)
        self.assertEquals(len(naily_master), 1)
        naily_workers = filter(lambda x: 'naily worker' in x, ps_output)
        logging.debug(
            "Found %d naily worker processes: %s" %
            (len(naily_workers), naily_workers))
        self.assertEqual(True, len(naily_workers) > 1)

if __name__ == '__main__':
    unittest.main()
