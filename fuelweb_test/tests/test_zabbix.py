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

import re

from devops.helpers.helpers import wait
from proboscis.asserts import assert_equal
from proboscis.asserts import assert_true
from proboscis import test

from fuelweb_test.helpers.decorators import log_snapshot_on_error
from fuelweb_test.helpers import checkers
from fuelweb_test import settings as hlp
from fuelweb_test.tests.base_test_case import SetupEnvironment
from fuelweb_test.tests.base_test_case import TestBasic
from fuelweb_test import logger

@test(groups=["thread_2"])
class SimpleZabbix(TestBasic):
    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["deploy_simple_zabbix"])
    @log_snapshot_on_error
    def deploy_simple_zabbix(self):
        """Deploy cluster in simple mode with zabbix-server

        Scenario:
            1. Setup master node
            2. Enable 'experimental' in Nailgun
            3. Restart Nailgun
            4. Create cluster
            5. Add 1 node with controller role
            6. Add 1 node with compute role
            7. Add 1 node with zabbix role
            8. Deploy the cluster
            9. Verify networks
            10. Check that zabbix server is running on the node
            11. Run OSTF
            12. Login in zabbix dashboard

        Snapshot: deploy_simple_zabbix

        """
        self.env.revert_snapshot("ready_with_3_slaves")

        node_ssh = self.env.get_ssh_to_remote(self.fuel_web.admin_node_ip)

        # Turn on experemntal mode
        checkers.check_enable_experimental_mode(
            node_ssh, '/etc/fuel/5.1/version.yaml')

        # restrat nailgun

        checkers.restart_nailgun(node_ssh)

        # check if zabbix role appears

        self.fuel_web.assert_release_role_present(
            release_name=hlp.OPENSTACK_RELEASE,
            role_name='zabbix-server')

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=hlp.DEPLOYMENT_MODE_SIMPLE,
            settings={
                'tenant': 'admin',
                'user': 'admin',
                'password': 'admin'
            }
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['compute'],
                'slave-03': ['zabbix-server']
            }
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)
        self.fuel_web.assert_cluster_ready(
            'slave-01', smiles_count=6, networks_count=1, timeout=300)

        self.fuel_web.verify_network(cluster_id)

        self.fuel_web.run_ostf(
            cluster_id=cluster_id)

        # login in dashboard
        node_ip = self.fuel_web.get_nailgun_node_by_devops_node(
            devops_node='slave-03')['ip']
            # self.environment.get_virtual_environment().
            # node_by_name(node_name))['ip']
        dashboard_url = 'http://{0}/zabbix'.format(node_ip)

        # get cred
        #login in dashboard




        self.env.make_snapshot("deploy_simple_zabbix")