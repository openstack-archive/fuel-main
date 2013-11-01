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


class TestCeph(BaseNodeTestCase):

    @logwrap
    def deploy_ceph_cluster(self, nodes, mode="multinode"):
        cluster_id = self.prepare_environment(settings={'nodes': nodes,
                                                        'volumes_ceph': True,
                                                        'images_ceph': True},
                                              save_state=False,
                                              mode=mode)
        return cluster_id

    @logwrap
    def check_ceph_ostf(self, cluster_id):
        self.run_OSTF(cluster_id=cluster_id, should_pass=18, should_fail=4)
        self._ostf_test_wait(cluster_id, 60*6)

    @logwrap
    def check_ceph_health(self, nodes):
        # Ssh to Ceph Monitor on a controller node:
        ssh = self._get_remote_for_role(nodes, 'controller')

        # Check Ceph node disk configuration:
        disks = ''.join(ssh.execute(
            'ceph osd tree list|grep osd')['stdout'])
        self.assertTrue('up' in disks)

        result = ''.join(ssh.execute('ceph health')['stdout'])
        self.assertEqual('HEALTH_OK', result)

    @snapshot_errors
    @logwrap
    @fetch_logs
    @attr(releases=['centos'], test_thread='thread_1')
    def test_ceph_multinode_compact(self):
        nodes = {'slave-01': ['controller', 'ceph-osd'],
                 'slave-02': ['compute', 'ceph-osd']}
        cluster_id = self.deploy_ceph_cluster(nodes)
        self.check_ceph_ostf(cluster_id)
        self.check_ceph_health(nodes)

    @snapshot_errors
    @logwrap
    @fetch_logs
    @attr(releases=['centos'], test_thread='thread_1')
    def test_ceph_multinode_with_cinder(self):
        nodes = {'slave-01': ['controller'],
                 'slave-02': ['compute'],
                 'slave-03': ['cinder', 'ceph-osd'],
                 'slave-04': ['cinder', 'ceph-osd']}
        cluster_id = self.deploy_ceph_cluster(nodes)
        self.check_ceph_ostf(cluster_id)
        self.check_ceph_health(nodes)

    @snapshot_errors
    @logwrap
    @fetch_logs
    @attr(releases=['centos'], test_thread='thread_1')
    def test_ceph_ha(self):
        nodes = {'slave-01': ['controller', 'ceph-osd'],
                 'slave-02': ['controller', 'ceph-osd'],
                 'slave-03': ['controller', 'ceph-osd'],
                 'slave-04': ['compute', 'ceph-osd'],
                 'slave-05': ['compute', 'ceph-osd'],
                 'slave-06': ['cinder', 'ceph-osd']}
        cluster_id = self.deploy_ceph_cluster(nodes, mode="ha_compact")
        self.check_ceph_ostf(cluster_id)
        self.check_ceph_health(nodes)

        # shut down an OSD node and rerun OSTF
        self.nodes().slaves[-1].destroy()
        self.check_ceph_ostf(cluster_id)

        # shut down a Monitor node and rerun OSTF
        self.nodes().slaves[1].destroy()
        self.check_ceph_ostf(cluster_id)

if __name__ == '__main__':
    unittest.main()
