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

from devops.helpers.helpers import wait
from devops.error import TimeoutError
from proboscis.asserts import assert_equal
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
        """Check l3-agent rescheduling after l3-agent dies

        Scenario:
            1. Create cluster. HA, Neutron with GRE segmentation
            2. Add 3 nodes with controller roles
            3. Add 2 nodes with compute roles
            4. Add 1 node with cinder role
            5. Deploy the cluster
            6. Manually reschedule router from primary controller
               to another one
            7. Stop l3-agent on new node with pcs
            8. Check l3-agent was rescheduled
            9. Check network connectivity from instance via
               dhcp namespace
            10. Run OSTF

        Snapshot deploy_ha_neutron

        """
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

        os_conn = os_actions.OpenStackActions(
            self.fuel_web.get_public_vip(cluster_id))

        net_id = os_conn.get_network('net04')['id']
        node = os_conn.get_node_with_dhcp_for_network(net_id)[0]
        node_fqdn = node.split('.')[0]
        logger.debug('node name with dhcp is {0}'.format(node_fqdn))

        devops_node = self.fuel_web.find_devops_node_by_nailgun_fqdn(
            node_fqdn, self.env.nodes().slaves[0:6])
        remote = self.env.get_ssh_to_remote_by_name(devops_node.name)

        dhcp_namespace = ''.join(remote.execute('ip netns | grep {0}'.format(
            net_id))['stdout']).rstrip()
        logger.debug('dhcp namespace is {0}'.format(dhcp_namespace))

        remote.execute(
            '. openrc;'
            ' nova keypair-add instancekey > /root/.ssh/webserver_rsa')
        remote.execute('chmod 400 /root/.ssh/webserver_rsa')

        instance = os_conn.create_server_for_migration(
            neutron=True, key_name='instancekey')
        instance_ip = instance.addresses['net04'][0]['addr']
        logger.debug('instance internal ip is {0}'.format(instance_ip))

        router_id = os_conn.get_routers_ids()[0]
        l3_agent_id = os_conn.get_l3_agent_ids(router_id)[0]
        logger.debug("l3 agent id is {0}".format(l3_agent_id))

        another_l3_agent = os_conn.get_available_l3_agents_ids(
            l3_agent_id)[0]
        logger.debug("another l3 agent is {0}".format(another_l3_agent))

        os_conn.remove_l3_from_router(l3_agent_id, router_id)
        os_conn.add_l3_to_router(another_l3_agent, router_id)
        wait(lambda: os_conn.get_l3_agent_ids(router_id), timeout=60 * 5)

        cmd = ". openrc; ip netns exec {0} ssh -i /root/.ssh/webserver_rsa" \
              " -o 'StrictHostKeyChecking no'" \
              " cirros@{1} \"ping -c 1 8.8.8.8\"".format(dhcp_namespace,
                                                         instance_ip)
        wait(lambda: remote.execute(cmd)['exit_code'] == 0, timeout=60)
        res = remote.execute(cmd)

        assert_equal(0, res['exit_code'],
                     'instance has no connectivity, exit code {0}'.format(
                         res['exit_code']))

        node_with_l3 = os_conn.get_l3_agent_hosts(router_id)[0]
        node_with_l3_fqdn = node_with_l3.split('.')[0]
        logger.debug("new node with l3 is {0}".format(node_with_l3_fqdn))

        new_devops = self.fuel_web.find_devops_node_by_nailgun_fqdn(
            node_with_l3_fqdn, self.env.nodes().slaves[0:6])
        new_remote = self.env.get_ssh_to_remote_by_name(new_devops.name)

        new_remote.execute("pcs resource ban p_neutron-l3-agent {0}".format(
            node_with_l3))

        try:
            wait(lambda: not node_with_l3 == os_conn.get_l3_agent_hosts(
                router_id)[0], timeout=60 * 3)
        except TimeoutError:
            raise TimeoutError(
                "l3 agent wasn't banned, it is still {0}".format(
                    os_conn.get_l3_agent_hosts(router_id)[0]))
        wait(lambda: os_conn.get_l3_agent_ids(router_id), timeout=60)

        res = remote.execute(cmd)
        assert_equal(0, res['exit_code'],
                     'instance has no connectivity, exit code is {0}'.format(
                         res['exit_code']))

        self.fuel_web.run_ostf(
            cluster_id=cluster_id,
            test_sets=['ha', 'smoke', 'sanity'])

        new_remote.execute("pcs resource clear p_neutron-l3-agent {0}".
                           format(node_with_l3))
