#    Copyright 2014 Mirantis, Inc.
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
from nose.tools import assert_equals

from proboscis import test

from fuelweb_test.helpers.decorators import log_snapshot_on_error
from fuelweb_test.helpers import checkers
from fuelweb_test.helpers import http
from fuelweb_test.helpers import os_actions
from fuelweb_test import settings as hlp
from fuelweb_test.tests.base_test_case import SetupEnvironment
from fuelweb_test.tests.base_test_case import TestBasic
from fuelweb_test import logger


@test(groups=["thread_2"])
class HAOneControllerZabbix(TestBasic):
    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["deploy_ha_one_controller_zabbix"])
    @log_snapshot_on_error
    def deploy_ha_one_controller_zabbix(self):
        """Deploy cluster in ha mode 1 controller with zabbix-server

        Scenario:
            1. Setup master node
            2. Enable 'experimental' in Nailgun
            3. Restart Nailgun
            4. Create cluster in ha mode with 1 controller
            5. Add 1 node with controller role
            6. Add 1 node with compute role
            7. Add 1 node with zabbix role
            8. Deploy the cluster
            9. Verify networks
            10. Check that zabbix server is running on the node
            11. Run OSTF
            12. Login in zabbix dashboard

        Duration 30m
        Snapshot: deploy_ha_one_controller_zabbix
        """
        self.env.revert_snapshot("ready_with_3_slaves")

        node_ssh = self.env.get_ssh_to_remote(self.fuel_web.admin_node_ip)

        # Turn on experimental mode
        checkers.check_enable_experimental_mode(
            node_ssh, '/etc/fuel/version.yaml')

        # restart nailgun

        checkers.restart_nailgun(node_ssh)

        # check if zabbix role appears

        self.fuel_web.assert_release_role_present(
            release_name=hlp.OPENSTACK_RELEASE,
            role_name='zabbix-server')

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=hlp.DEPLOYMENT_MODE,
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
        os_conn = os_actions.OpenStackActions(
            self.fuel_web.get_public_vip(cluster_id))
        self.fuel_web.assert_cluster_ready(
            os_conn, smiles_count=6, networks_count=1, timeout=300)

        self.fuel_web.verify_network(cluster_id)

        self.fuel_web.run_ostf(
            cluster_id=cluster_id)

        # login in dashboard
        node_ip = self.fuel_web.get_nailgun_node_by_devops_node(
            self.env.get_virtual_environment().get_node(name='slave-03'))['ip']

        dashboard_url = 'http://{0}/zabbix/'.format(node_ip)

        logger.debug("Zabbix dashboard {0}".format(dashboard_url))

        login_data = {'username': 'admin', 'password': 'zabbix'}

        zab_client = http.HTTPClientZabbix(url=dashboard_url)
        login_resp = zab_client.post(endpoint='index.php', data=login_data)
        assert_equals(login_resp.code, 200)
        assert_equals(login_resp.msg, 'OK')
        event_resp = zab_client.get(
            endpoint='events.php',
            cookie=login_resp.headers.get('Set-Cookie'))
        assert_equals(event_resp.code, 200)

        self.env.make_snapshot("deploy_ha_one_controller_zabbix")
