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

from fuelweb_test.helpers.decorators import log_snapshot_on_error, debug
from fuelweb_test import settings
from fuelweb_test.settings import DEPLOYMENT_MODE_HA
from fuelweb_test.tests.base_test_case import TestBasic, SetupEnvironment

from proboscis import test, SkipTest

logger = logging.getLogger(__name__)
logwrap = debug(logger)


@test(groups=["thread_5", "test_strange_mixed"])
class MixedCases(TestBasic):

    @test(depends_on=[SetupEnvironment.prepare_release],
          groups=["mixed_nine_nodes"])
    @log_snapshot_on_error
    def mixed_nine_nodes(self):
        """Deploy cluster with mixed roles on 9 nodes in HA mode

        Scenario:
            1. Create cluster
            2. Add 4 nodes as controllers and ceph OSD roles
            3. Add 5 nodes with compute role and ceph OSD roles
            4. Turn on Savanna and Ceilometer
            5. Deploy the cluster
            6. Check networks and OSTF

        Snapshot None

        """
        if settings.OPENSTACK_RELEASE == settings.OPENSTACK_RELEASE_REDHAT:
            raise SkipTest()

        self.env.revert_snapshot("ready")
        self.env.bootstrap_nodes(self.env.nodes().slaves[:9])

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE_HA,
            settings={
                'volumes_ceph': True,
                'images_ceph': True,
                'savanna': True,
                'ceilometer': True
            }
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller', 'ceph-osd'],
                'slave-02': ['controller', 'ceph-osd'],
                'slave-03': ['controller', 'ceph-osd'],
                'slave-04': ['controller', 'ceph-osd'],
                'slave-05': ['compute', 'cinder', 'ceph-osd'],
                'slave-05': ['compute', 'cinder', 'ceph-osd'],
                'slave-05': ['compute', 'cinder', 'ceph-osd'],
                'slave-05': ['compute', 'cinder', 'ceph-osd'],
                'slave-05': ['compute', 'cinder', 'ceph-osd']
            }
        )
        # Cluster deploy
        self.fuel_web.deploy_cluster_wait(cluster_id)

        # Warm restart
        # self.fuel_web.warm_restart_nodes(self.env.nodes().slaves[:4])
        # check_ceph_health(self.env.get_ssh_to_remote_by_name('slave-01'))
        self.fuel_web.run_ostf(
            cluster_id=cluster_id,
            should_fail=4)
