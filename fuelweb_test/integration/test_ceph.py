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

    def ceph_simple(self, cluster_name, nodes):
        self.prepare_environment()

        # create a new empty cluster and add nodes to it:
        cluster_id = self.create_cluster(name=cluster_name)
        self.bootstrap_nodes(self.nodes().slaves[:4])
        self.update_nodes(cluster_id, nodes)

        # deploy cluster:
        task = self.deploy_cluster(cluster_id)
        self.assertTaskSuccess(task)

        self.run_OSTF(cluster_id=cluster_id, should_pass=20, should_fail=4)
        self._ostf_test_wait(cluster_id, 60*6)

        # Ssh to controller node:
        ssh = self._get_remote_for_node(self.nodes().slaves[1].name)
        # Check Ceph node disk configuration:
        disks = ''.join(ssh.execute(
            'ceph-deploy disk list %s' %
            self.nodes().slaves[4].name)['stdout'])
        self.assertTrue('xfs' in disks)

        # SSH to node with Ceph and run Ceph health check:
        ssh = self._get_remote_for_node(self.nodes().slaves[4].name)
        # ssh = self._get_remote(nodes().slaves[4]['ip'])
        result = "".join(ssh.execute('ceph health')['stdout'])
        self.assertEqual('HEALTH_OK', result)

    @snapshot_errors
    @logwrap
    @fetch_logs
    @attr(releases=['centos', 'ubuntu'], test_thread='thread_1')
    def test_simple_ceph_compute(self):
        self.ceph_simple(
            cluster_name="simple_ceph_compute",
            nodes={
                'slave-01': ['controller'],
                'slave-02': ['compute'],
                'slave-03': ['cinder'],
                'slave-04': ['compute', 'ceph-osd']
            }
        )

    @snapshot_errors
    @logwrap
    @fetch_logs
    @attr(releases=['centos', 'ubuntu'], test_thread='thread_1')
    def test_simple_ceph_cinder(self):
        self.ceph_simple(
            cluster_name="simple_ceph_cinder",
            nodes={
                'slave-01': ['controller'],
                'slave-02': ['compute'],
                'slave-03': ['compute'],
                'slave-04': ['cinder', 'ceph-osd']
            }
        )

    @snapshot_errors
    @logwrap
    @fetch_logs
    @attr(releases=['centos', 'ubuntu'], test_thread='thread_1')
    def test_ha_ceph(self):
        cluster_name = 'ceph_multinode'

        nodes = {'slave-01': ['controller'],
                 'slave-02': ['controller'],
                 'slave-03': ['controller'],
                 'slave-04': ['compute', 'ceph-osd'],
                 'slave-05': ['compute', 'ceph-osd'],
                 'slave-06': ['cinder', 'ceph-osd']}

        self.prepare_environment()

        # create a new empty cluster and add nodes to it:
        cluster_id = self.create_cluster(
            name=cluster_name,
            mode="ha_compact"
        )
        self.bootstrap_nodes(self.nodes().slaves[:6])
        self.update_nodes(cluster_id, nodes)

        # deploy cluster:
        task = self.deploy_cluster(cluster_id)
        self.assertTaskSuccess(task)

        # run OSTF
        self.run_OSTF(cluster_id=cluster_id, should_pass=20, should_fail=4)
        self._ostf_test_wait(cluster_id, 60*6)

        # shut down one ceph nodes
        self.nodes().slaves[6].destroy()

        # run OSTF again
        self.run_OSTF(cluster_id=cluster_id, should_pass=20, should_fail=4)
        self._ostf_test_wait(cluster_id, 60*6)

        # validate Ceph is operational:
        ssh = self._get_remote_for_node(self.nodes().slaves[4].name)
        result = "".join(ssh.execute('ceph health')['stdout'])
        self.assertEqual('HEALTH_OK', result)

if __name__ == '__main__':
    unittest.main()