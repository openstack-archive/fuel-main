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
import os
import traceback

from devops.helpers.helpers import wait
from proboscis import asserts
from proboscis import test

from fuelweb_test.helpers.decorators import log_snapshot_on_error
from fuelweb_test.helpers import os_actions
from fuelweb_test.helpers import checkers
from fuelweb_test import logger
from fuelweb_test.settings import DEPLOYMENT_MODE_SIMPLE
from fuelweb_test.settings import LBAAS_PLUGIN_PATH
from fuelweb_test.settings import NEUTRON_SEGMENT_TYPE
from fuelweb_test.tests.base_test_case import SetupEnvironment
from fuelweb_test.tests.base_test_case import TestBasic


@test(enabled=False, groups=["plugins"])
class LbaasPlugin(TestBasic):
    @classmethod
    def check_neutron_agents_statuses(cls, os_conn):
        agents_list = os_conn.list_agents()

        for a in agents_list['agents']:
            asserts.assert_equal(
                a['alive'], True,
                'Neutron agent {0} is not alive'. format(a['binary']))
            asserts.assert_true(
                a['admin_state_up'],
                "Admin state is down for agent {0}".format(a['binary']))

        lb_agent = [a for a in agents_list["agents"]
                    if a['binary'] == 'neutron-lbaas-agent']

        logger.debug("LbaaS agent list is {0}".format(lb_agent))

        asserts.assert_equal(
            len(lb_agent), 1,
            'There is not LbaaS agent in neutron agent list output')

    @classmethod
    def check_lbass_work(cls, os_conn):
        # create pool
        pool = os_conn.create_pool(pool_name='lbaas_pool')

        logger.debug('pull is {0}'.format(pool))

        # create vip
        vip = os_conn.create_vip(name='lbaas_vip',
                                 protocol='HTTP',
                                 port=80,
                                 pool=pool)

        logger.debug('vip is {0}'.format(vip))

        # get list of vips
        lb_vip_list = os_conn.get_vips()

        logger.debug(
            'Initial state of vip is {0}'.format(
                os_conn.get_vip(lb_vip_list['vips'][0]['id'])))

        # wait for active status
        try:
            wait(lambda: os_conn.get_vip(
                lb_vip_list['vips'][0]['id'])['vip']['status'] == 'ACTIVE',
                timeout=120 * 60)
        except:
            logger.error(traceback.format_exc())
            vip_state = os_conn.get_vip(
                lb_vip_list['vips'][0]['id'])['vip']['status']
            asserts.assert_equal(
                'ACTIVE', vip_state,
                "Vip is not active, current state is {0}".format(vip_state))

    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["deploy_neutron_lbaas_simple"])
    @log_snapshot_on_error
    def deploy_neutron_lbaas_simple(self):
        """Deploy cluster in simple mode with LbaaS plugin

        Scenario:
            1. Upload plugin to the master node
            2. Install plugin
            3. Create cluster
            4. Add 1 node with controller role
            5. Add 2 nodes with compute role
            6. Deploy the cluster
            7. Run network verification
            8. Check health of lbaas agent on the node
            9. Create pool and vip
            10. Run OSTF

        Duration 35m
        Snapshot deploy_neutron_vlan_lbaas_simple

        """
        self.env.revert_snapshot("ready_with_3_slaves")

        # copy plugin to the master node

        checkers.upload_tarball(
            self.env.get_admin_remote(), LBAAS_PLUGIN_PATH, '/var')

        # install plugin

        checkers.install_plugin_check_code(
            self.env.get_admin_remote(),
            plugin=os.path.basename(LBAAS_PLUGIN_PATH))

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE_SIMPLE,
            settings={
                "net_provider": 'neutron',
                "net_segment_type": NEUTRON_SEGMENT_TYPE,
            }
        )

        attr = self.fuel_web.client.get_cluster_attributes(cluster_id)
        if 'lbaas' in attr['editable']:
            logger.debug('we have lbaas element')
            plugin_data = attr['editable']['lbaas']['metadata']
            plugin_data['enabled'] = True

        self.fuel_web.client.update_cluster_attributes(cluster_id, attr)

        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['compute'],
                'slave-03': ['compute']
            }
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)

        cluster = self.fuel_web.client.get_cluster(cluster_id)
        asserts.assert_equal(str(cluster['net_provider']), 'neutron')

        self.fuel_web.verify_network(cluster_id)

        controller = self.fuel_web.get_nailgun_node_by_name('slave-01')
        os_conn = os_actions.OpenStackActions(controller['ip'])

        self.check_neutron_agents_statuses(os_conn)

        self.check_lbass_work(os_conn)

        self.fuel_web.run_ostf(
            cluster_id=cluster_id)

        self.env.make_snapshot("deploy_neutron_vlan_lbaas_simple")

    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["deploy_neutron_lbaas_simple_reset_ready"])
    @log_snapshot_on_error
    def deploy_neutron_lbaas_simple_reset_ready(self):
        """Deploy and re-deploy cluster in simple mode with LbaaS plugin

        Scenario:
            1. Upload plugin to the master node
            2. Install plugin
            3. Create cluster
            4. Add 1 node with controller role
            5. Add 1 nodes with compute role
            6. Deploy the cluster
            7. Run network verification
            8. Check health of lbaas agent on the node
            9. Create pool and vip
            10. Reset cluster
            11. Add 1 compute
            12. Re-deploy cluster
            13. Check health of lbaas agent on the node
            14. Create pool and vip
            15. Run OSTF

        Duration 65m
        Snapshot deploy_neutron_lbaas_simple_reset_ready

        """
        self.env.revert_snapshot("ready_with_3_slaves")

        # copy plugin to the master node

        checkers.upload_tarball(
            self.env.get_admin_remote(), LBAAS_PLUGIN_PATH, '/var')

        # install plugin

        checkers.install_plugin_check_code(
            self.env.get_admin_remote(),
            plugin=os.path.basename(LBAAS_PLUGIN_PATH))

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE_SIMPLE,
            settings={
                "net_provider": 'neutron',
                "net_segment_type": NEUTRON_SEGMENT_TYPE,
            }
        )

        attr = self.fuel_web.client.get_cluster_attributes(cluster_id)
        if 'lbaas' in attr['editable']:
            logger.debug('we have lbaas element')
            plugin_data = attr['editable']['lbaas']['metadata']
            plugin_data['enabled'] = True

        self.fuel_web.client.update_cluster_attributes(cluster_id, attr)

        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['compute'],
            }
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)

        cluster = self.fuel_web.client.get_cluster(cluster_id)
        asserts.assert_equal(str(cluster['net_provider']), 'neutron')

        self.fuel_web.verify_network(cluster_id)

        controller = self.fuel_web.get_nailgun_node_by_name('slave-01')
        os_conn = os_actions.OpenStackActions(controller['ip'])

        self.check_neutron_agents_statuses(os_conn)

        self.check_lbass_work(os_conn)

        self.fuel_web.stop_reset_env_wait(cluster_id)

        self.fuel_web.wait_nodes_get_online_state(
            self.env.get_virtual_environment().nodes().slaves[:2])

        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-03': ['compute'],
            }
        )

        self.fuel_web.deploy_cluster_wait(cluster_id)

        self.check_neutron_agents_statuses(os_conn)

        self.check_lbass_work(os_conn)
        self.fuel_web.run_ostf(
            cluster_id=cluster_id)

        self.env.make_snapshot("deploy_neutron_lbaas_simple_reset_ready")
