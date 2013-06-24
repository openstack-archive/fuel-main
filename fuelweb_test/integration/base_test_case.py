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


from devops.helpers.helpers import SSHClient
import logging
from unittest.case import TestCase
from fuelweb_test.integration.ci_fuel_web import CiFuelWeb


logging.basicConfig(format=':%(lineno)d: %(asctime)s %(message)s',
                    level=logging.DEBUG)


class BaseTestCase(TestCase):
    def ci(self):
        if not hasattr(self, '_ci'):
            self._ci = CiFuelWeb()
        return self._ci

    def environment(self):
        return self.ci().environment()

    def nodes(self):
        return self.ci().nodes()

    def remote(self):
        """
        :rtype : SSHClient
        """
        return self.nodes().admin.remote(
            'internal',
            login='root',
            password='r00tme')

    def get_admin_node_ip(self):
        return str(
            self.nodes().admin.get_ip_address_by_network_name('internal'))
