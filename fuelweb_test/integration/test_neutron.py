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
from nose.plugins.attrib import attr
from fuelweb_test.integration.base_node_test_case import BaseNodeTestCase
from fuelweb_test.integration.decorators import snapshot_errors, \
    debug, fetch_logs

logging.basicConfig(
    format=':%(lineno)d: %(asctime)s %(message)s',
    level=logging.DEBUG
)

logger = logging.getLogger(__name__)
logwrap = debug(logger)


class TestNode(BaseNodeTestCase):
    @snapshot_errors
    @logwrap
    @fetch_logs
    @attr(releases=['centos', 'ubuntu'], test_thread='thread_3')
    def test_neutron_gre(self):
        cluster_id = self.prepare_environment(name='test_neutron_gre_deployment',
                                              mode="multinode",
                                              settings={
                                                  'nodes': {
                                                      'slave-01': ['controller'],
                                                      'slave-04': ['compute'],
                                                      'slave-05': ['compute'],
                                                      },
                                                  'net_provider': 'neutron',
                                                  'net_segment_type': 'gre',
                                                  })
        cluster = self.client.get_cluster(cluster_id)
        self.assertEqual(str(cluster['net_provider']), 'neutron')
        self.assertEqual(str(cluster['net_segment_type']), 'gre')

        self.run_OSTF(cluster_id=cluster_id)

    @snapshot_errors
    @logwrap
    @fetch_logs
    @attr(releases=['centos', 'ubuntu'], test_thread='thread_3')
    def test_neutron_vlan(self):
        cluster_id = self.prepare_environment(name='test_neutron_gre_deployment',
                                              mode="multinode",
                                              settings={
                                                  'nodes': {
                                                      'slave-01': ['controller'],
                                                      'slave-04': ['compute'],
                                                      'slave-05': ['compute'],
                                                      },
                                                  'net_provider': 'neutron',
                                                  'net_segment_type': 'vlan',
                                                  })
        cluster = self.client.get_cluster(cluster_id)
        self.assertEqual(str(cluster['net_provider']), 'neutron')
        self.assertEqual(str(cluster['net_segment_type']), 'vlan')

        self.run_OSTF(cluster_id=cluster_id)
