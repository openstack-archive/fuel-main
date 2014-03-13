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
import time
import re

from devops.helpers.helpers import wait
from proboscis import test

from fuelweb_test import settings
from fuelweb_test.helpers.decorators import debug
from fuelweb_test.helpers.decorators import log_snapshot_on_error
from fuelweb_test.tests.base_test_case import SetupEnvironment, TestBasic

logger = logging.getLogger(__name__)
logwrap = debug(logger)


@test(groups=["thread_5", "ha"])
class TestNeutronFailover(TestBasic):

    @test(depends_on=[SetupEnvironment.prepare_slaves_5],
          groups=["deploy_ha_neutron"])
    @log_snapshot_on_error
    def deploy_ha_neutron(self):
        """Deploy cluster in HA mode, Neutron with GRE segmentation

        Scenario:
            1. Create cluster. HA, Neutron with GRE segmentation
            2. Add 3 nodes with controller roles
            3. Add 2 nodes with compute roles
            4. Deploy the cluster
            5. Destroy controller with running l3 agent
            6. Wait for OFFLINE of the controller at fuel UI
            7. Run instance connectivity OSTF tests

        Snapshot deploy_ha_neutron

        """
        self.env.revert_snapshot("ready_with_5_slaves")

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=settings.DEPLOYMENT_MODE_HA,
            settings={
                "net_provider": 'neutron',
                "net_segment_type": 'gre'
            }
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['controller'],
                'slave-03': ['controller'],
                'slave-04': ['compute'],
                'slave-05': ['compute']
            }
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)

        # Look for controller with l3 agent
        ret = self.fuel_web.get_pacemaker_status(
            self.env.nodes().slaves[0].name)
        fqdn = re.search(
            'p_neutron-l3-agent\s+\(ocf::mirantis:neutron-agent-l3\):\s+'
            'Started (node-\d+)', ret).group(1)
        devops_node = self.fuel_web.find_devops_node_by_nailgun_fqdn(
            fqdn, self.env.nodes().slaves)
        # Destroy it and wait for OFFLINE status at fuel UI
        devops_node.destroy()
        # sleep max(op monitor interval)
        time.sleep(60 * 2)
        wait(lambda: not self.fuel_web.get_nailgun_node_by_devops_node(
            devops_node)['online'])

        cluster_id = \
            self.fuel_web.client.get_cluster_id(self.__class__.__name__)
        self.fuel_web.run_single_ostf_test(
            cluster_id=cluster_id, test_sets=['smoke'],
            test_name=('fuel_health.tests.smoke.test_nova_create_instance_'
                       'with_connectivity.TestNovaNetwork.test_008_check_'
                       'public_instance_connectivity_from_instance'))
