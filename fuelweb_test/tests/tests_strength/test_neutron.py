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

import time
import re

from devops.helpers.helpers import wait
from devops.error import TimeoutError
from proboscis import asserts
from proboscis.asserts import assert_equal
from proboscis import SkipTest
from proboscis import test
from fuelweb_test import logger
from fuelweb_test import settings
from fuelweb_test.helpers.decorators import log_snapshot_on_error
from fuelweb_test.helpers import os_actions
from fuelweb_test.tests import base_test_case


@test(groups=["thread_5", "ha"])
class TestNeutronFailover(base_test_case.TestBasic):

    @test(depends_on=[base_test_case.SetupEnvironment.prepare_release],
          groups=["deploy_ha_neutron"])
    @log_snapshot_on_error
    def deploy_ha_neutron(self):
        """Deploy cluster in HA mode, Neutron with GRE segmentation

        Scenario:
            1. Create cluster. HA, Neutron with GRE segmentation
            2. Add 3 nodes with controller roles
            3. Add 2 nodes with compute roles
            4. Add 1 node with cinder role
            5. Deploy the cluster

        Snapshot deploy_ha_neutron

        """
        try:
            self.check_run('deploy_ha_neutron')
        except SkipTest:
            return
        self.env.revert_snapshot("ready")
        self.env.bootstrap_nodes(self.env.nodes().slaves[:6])

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
                'slave-05': ['compute'],
                'slave-06': ['cinder']
            }
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)
        self.env.make_snapshot("deploy_ha_neutron", is_make=True)

    @test(depends_on=[deploy_ha_neutron],
          groups=["neutron_l3_migration"])
    @log_snapshot_on_error
    def neutron_l3_migration(self):
        """Check l3 agent migration after destroy controller

        Scenario:
            1. Revert snapshot with Neutron GRE cluster
            2. Destroy controller with running l3 agent
            3. Wait for OFFLINE of the controller at fuel UI
            4. Run instance connectivity OSTF tests

        Snapshot deploy_ha_neutron

        """
        self.env.revert_snapshot("deploy_ha_neutron")

        # Look for controller with l3 agent
        ret = self.fuel_web.get_pacemaker_status(
            self.env.nodes().slaves[0].name)
        logger.debug('pacemaker state before fail is {0}'.format(ret))
        fqdn = re.search(
            'p_neutron-l3-agent\s+\(ocf::mirantis:neutron-agent-l3\):\s+'
            'Started (node-\d+)', ret).group(1)
        logger.debug('fdqn before fail is {0}'.format(fqdn))
        devops_node = self.fuel_web.find_devops_node_by_nailgun_fqdn(
            fqdn, self.env.nodes().slaves)
        logger.debug('devops node name before fail is {0}'.format(
            devops_node.name))
        # Destroy it and wait for OFFLINE status at fuel UI
        devops_node.destroy()
        # sleep max(op monitor interval)
        time.sleep(60 * 2)
        wait(lambda: not self.fuel_web.get_nailgun_node_by_devops_node(
            devops_node)['online'], timeout=60 * 10)

        remains_online_nodes = \
            [node for node in self.env.nodes().slaves[0:3]
             if self.fuel_web.get_nailgun_node_by_devops_node(node)['online']]
        logger.debug('Online nodes are {0}'.format(
            [node.name for node in remains_online_nodes]))
        # Look for controller with l3 agent one more time
        ret = self.fuel_web.get_pacemaker_status(remains_online_nodes[0].name)
        fqdn = re.search(
            'p_neutron-l3-agent\s+\(ocf::mirantis:neutron-agent-l3\):\s+'
            'Started (node-\d+)', ret).group(1)

        logger.debug('fqdn with l3 after fail is {0}'.format(fqdn))

        devops_node = self.fuel_web.find_devops_node_by_nailgun_fqdn(
            fqdn, self.env.nodes().slaves)

        logger.debug('Devops node with recovered l3 is {0}'.format(
            devops_node.name))

        asserts.assert_true(
            devops_node.name in [node.name for node in remains_online_nodes])

        cluster_id = self.fuel_web.client.get_cluster_id(
            self.__class__.__name__)

        self.fuel_web.run_ostf(
            cluster_id=cluster_id,
            test_sets=['ha', 'smoke', 'sanity'],
            should_fail=1,
            failed_test_name=['Check that required services are running'])

    @test(depends_on=[deploy_ha_neutron],
          groups=["check_agents_migration"])
    @log_snapshot_on_error
    def check_agents_migration(self):
        """Check instance connectivity after neutron agents migration

        Scenario:
            1. Revert snapshot with Neutron GRE cluster
            2. Create instance and assign floating ip to it
            3. Add collocation between l3-agent and dhcp-agent
            4. Create agents_migration snapshot
            5. 10 times revert snapshot agents_migration
            6. Migrate manually dhcp-agent and l3-agent
            7. Check ping to floating ip
            8. In case of failure increase number of failures
            9. Restart openvswitch-agent on node with l3 agent
            10. Ping floating ip again
            11. In case of success increase number of workarounds on 1
            12. In case of failure increase number of failed workarounds on 1

        Snapshot deploy_ha_neutron

        """
        self.env.revert_snapshot("deploy_ha_neutron")

        if settings.OPENSTACK_RELEASE_UBUNTU in settings.OPENSTACK_RELEASE:
            restart_openvswitch = "crm resource restart" \
                                  " clone_p_neutron-plugin-openvswitch-agent"
        else:
            restart_openvswitch = "crm resource restart" \
                                  " clone_p_neutron-openvswitch-agent"
        cluster_id = self.fuel_web.get_last_created_cluster()
        os_conn = os_actions.OpenStackActions(
            self.fuel_web.get_public_vip(cluster_id))

        router_id = os_conn.get_routers_ids()[0]
        node_with_l3 = os_conn.get_l3_agent_hosts(router_id)[0]
        logger.debug("node with l3 agent is {0}".format(node_with_l3))

        net_id = os_conn.get_network('net04')['id']
        node_with_dhcp = os_conn.get_node_with_dhcp_for_network(net_id)[0]
        logger.debug("node with dhcp agent is {0}".format(node_with_dhcp))

        remote = self.env.get_ssh_to_remote_by_name("slave-01")

        instance = os_conn.create_server_for_migration(
            neutron=True)
        floating_ip = os_conn.assign_floating_ip(instance)
        logger.debug('instance floating ip is {0}'.format(floating_ip.ip))

        cmd = "ping -i 10 -c 1 -W 10 -w 60 {0}".format(floating_ip.ip)

        try:
            wait(lambda: remote.execute(cmd)['exit_code'] == 0, timeout=180)
        except TimeoutError:
            pass

        res = remote.execute(cmd)
        logger.debug("command execution {0}".format(res))
        assert_equal(0, res['exit_code'],
                     'floating ip is not pingable, exit code {0}'.format(
                         res['exit_code']))

        remote.execute("pcs constraint colocation add p_neutron-l3-agent"
                       " with p_neutron-dhcp-agent score=-INFINITY")

        self.env.make_snapshot("agents_migration", is_make=True)

        failures = 0
        workarounds = 0
        failed_workarounds = 0

        for i in range(0, 10):
            self.env.revert_snapshot("agents_migration")
            os_conn = os_actions.OpenStackActions(
                self.fuel_web.get_public_vip(cluster_id))
            remote = self.env.get_ssh_to_remote_by_name('slave-01')
            remote.execute("pcs constraint location p_neutron-dhcp-agent"
                           " prefers {0}=-INFINITY".format(node_with_dhcp))
            wait((lambda:
                 not node_with_dhcp == os_conn.get_node_with_dhcp_for_network(
                     net_id)[0]
                 if os_conn.get_node_with_dhcp_for_network(net_id)
                 else False),
                 timeout=60 * 3)

            remote.execute("pcs constraint location p_neutron-l3-agent"
                           " prefers {0}=-INFINITY".format(node_with_l3))
            wait((lambda:
                 not node_with_l3 == os_conn.get_l3_agent_hosts(router_id)[0]
                 if os_conn.get_l3_agent_hosts(router_id) else False),
                 timeout=60 * 3)

            node_with_l3 = os_conn.get_l3_agent_hosts(router_id)[0]
            if settings.OPENSTACK_RELEASE_UBUNTU in \
                    settings.OPENSTACK_RELEASE:
                node_fqdn = node_with_l3
            else:
                node_fqdn = node_with_l3.split(".")[0]
            logger.debug("node fqdn is {0}".format(node_fqdn))
            devops_node = self.fuel_web.find_devops_node_by_nailgun_fqdn(
                node_fqdn, self.env.nodes().slaves[0:6])
            l3_node_remote = self.env.get_ssh_to_remote_by_name(
                devops_node.name)

            res = l3_node_remote.execute(cmd)
            logger.debug("connectivity after migration is {0}".format(res))
            if res['exit_code'] != 0:
                failures += 1
                l3_node_remote.execute(restart_openvswitch)
                res = l3_node_remote.execute(cmd)
                if res['exit_code'] != 0:
                    failed_workarounds += 1
                else:
                    workarounds += 1

        logger.info("total number of failures is {0}".format(failures))
        logger.info("number of successful workarounds is {0}".format(
            workarounds))
        logger.info("number of unsuccessful workarounds is {0}".format(
            failed_workarounds))
