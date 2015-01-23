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
from proboscis import SkipTest
from proboscis import test

from fuelweb_test import logger
from fuelweb_test import settings
from fuelweb_test.helpers.decorators import log_snapshot_on_error
from fuelweb_test.helpers.decorators import retry
from fuelweb_test.helpers import os_actions
from fuelweb_test.tests import base_test_case


@test(groups=["thread_5", "ha"])
class TestNeutronFailover(base_test_case.TestBasic):

    @classmethod
    def get_node_with_dhcp(cls, self, os_conn, net_id):
        node = os_conn.get_node_with_dhcp_for_network(net_id)[0]
        node_fqdn = self.fuel_web.get_fqdn_by_hostname(node)
        logger.debug('node name with dhcp is {0}'.format(node))
        devops_node = self.fuel_web.find_devops_node_by_nailgun_fqdn(
            node_fqdn, self.env.get_virtual_environment(
            ).nodes().slaves[0:6])
        return devops_node

    @classmethod
    def get_node_with_l3(cls, self, node_with_l3):
        node_with_l3_fqdn = self.fuel_web.get_fqdn_by_hostname(node_with_l3)
        logger.debug("new node with l3 is {0}".format(node_with_l3))
        devops_node = self.fuel_web.find_devops_node_by_nailgun_fqdn(
            node_with_l3_fqdn,
            self.env.get_virtual_environment().nodes().slaves[0:6])
        return devops_node

    @classmethod
    def create_instance_with_keypair(cls, os_conn, remote):
        remote.execute(
            '. openrc;'
            ' nova keypair-add instancekey > /root/.ssh/webserver_rsa')
        remote.execute('chmod 400 /root/.ssh/webserver_rsa')
        instance = os_conn.create_server_for_migration(
            neutron=True, key_name='instancekey')
        return instance

    @classmethod
    def reshedule_router_manually(cls, os_conn, router_id):
        l3_agent_id = os_conn.get_l3_agent_ids(router_id)[0]
        logger.debug("l3 agent id is {0}".format(l3_agent_id))

        another_l3_agent = os_conn.get_available_l3_agents_ids(
            l3_agent_id)[0]
        logger.debug("another l3 agent is {0}".format(another_l3_agent))

        os_conn.remove_l3_from_router(l3_agent_id, router_id)
        os_conn.add_l3_to_router(another_l3_agent, router_id)
        wait(lambda: os_conn.get_l3_agent_ids(router_id), timeout=60 * 5)

    @classmethod
    def check_instance_connectivity(cls, remote, dhcp_namespace, instance_ip):
        cmd = ". openrc; ip netns exec {0} ssh -i /root/.ssh/webserver_rsa" \
              " -o 'StrictHostKeyChecking no'" \
              " cirros@{1} \"ping -c 1 8.8.8.8\"".format(dhcp_namespace,
                                                         instance_ip)
        wait(lambda: remote.execute(cmd)['exit_code'] == 0, timeout=2 * 60)
        res = remote.execute(cmd)
        assert_equal(0, res['exit_code'],
                     'instance has no connectivity, exit code {0}'.format(
                         res['exit_code']))

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

        Duration 90m
        Snapshot deploy_ha_neutron

        """
        try:
            self.check_run('deploy_ha_neutron')
        except SkipTest:
            return
        self.env.revert_snapshot("ready")
        self.env.bootstrap_nodes(
            self.env.get_virtual_environment().nodes().slaves[:6])

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=settings.DEPLOYMENT_MODE,
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
        """Check l3-agent rescheduling after l3-agent dies

        Scenario:
            1. Revert snapshot with neutron cluster
            2. Manually reschedule router from primary controller
               to another one
            3. Stop l3-agent on new node with pcs
            4. Check l3-agent was rescheduled
            5. Check network connectivity from instance via
               dhcp namespace
            6. Run OSTF
        Duration 30m
        """
        self.env.revert_snapshot("deploy_ha_neutron")
        cluster_id = self.fuel_web.get_last_created_cluster()
        os_conn = os_actions.OpenStackActions(
            self.fuel_web.get_public_vip(cluster_id))

        net_id = os_conn.get_network('net04')['id']
        devops_node = self.get_node_with_dhcp(self, os_conn, net_id)
        remote = self.env.get_ssh_to_remote_by_name(devops_node.name)

        dhcp_namespace = ''.join(remote.execute('ip netns | grep {0}'.format(
            net_id))['stdout']).rstrip()
        logger.debug('dhcp namespace is {0}'.format(dhcp_namespace))

        instance_ip = \
            self.create_instance_with_keypair(
                os_conn, remote).addresses['net04'][0]['addr']
        logger.debug('instance internal ip is {0}'.format(instance_ip))

        router_id = os_conn.get_routers_ids()[0]
        self.reshedule_router_manually(os_conn, router_id)
        self.check_instance_connectivity(remote, dhcp_namespace, instance_ip)

        node_with_l3 = os_conn.get_l3_agent_hosts(router_id)[0]
        new_devops = self.get_node_with_l3(self, node_with_l3)
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

        self.check_instance_connectivity(remote, dhcp_namespace, instance_ip)

        self.fuel_web.run_ostf(
            cluster_id=cluster_id,
            test_sets=['ha', 'smoke', 'sanity'])

        new_remote.execute("pcs resource clear p_neutron-l3-agent {0}".
                           format(node_with_l3))

    @test(depends_on=[deploy_ha_neutron],
          groups=["neutron_l3_migration_after_reset"])
    @log_snapshot_on_error
    def neutron_l3_migration_after_reset(self):
        """Check l3-agent rescheduling after reset non-primary controller

        Scenario:
            1. Revert snapshot with neutron cluster
            2. Manually reschedule router from primary controller
               to another one
            3. Reset controller with l3-agent
            4. Check l3-agent was rescheduled
            5. Check network connectivity from instance via
               dhcp namespace
            6. Run OSTF

        Duration 30m
        """
        self.env.revert_snapshot("deploy_ha_neutron")
        cluster_id = self.fuel_web.get_last_created_cluster()
        os_conn = os_actions.OpenStackActions(
            self.fuel_web.get_public_vip(cluster_id))

        net_id = os_conn.get_network('net04')['id']
        devops_node = self.get_node_with_dhcp(self, os_conn, net_id)
        remote = self.env.get_ssh_to_remote_by_name(devops_node.name)

        dhcp_namespace = ''.join(remote.execute('ip netns | grep {0}'.format(
            net_id))['stdout']).rstrip()
        logger.debug('dhcp namespace is {0}'.format(dhcp_namespace))

        instance_ip = \
            self.create_instance_with_keypair(
                os_conn, remote).addresses['net04'][0]['addr']
        logger.debug('instance internal ip is {0}'.format(instance_ip))

        router_id = os_conn.get_routers_ids()[0]
        self.reshedule_router_manually(os_conn, router_id)
        self.check_instance_connectivity(remote, dhcp_namespace, instance_ip)

        node_with_l3 = os_conn.get_l3_agent_hosts(router_id)[0]
        new_devops = self.get_node_with_l3(self, node_with_l3)
        self.fuel_web.warm_restart_nodes([new_devops])

        try:
            wait(lambda: not node_with_l3 == os_conn.get_l3_agent_hosts(
                router_id)[0], timeout=60 * 3)
        except TimeoutError:
            raise TimeoutError(
                "l3 agent wasn't rescheduled, it is still {0}".format(
                    os_conn.get_l3_agent_hosts(router_id)[0]))
        wait(lambda: os_conn.get_l3_agent_ids(router_id), timeout=60)

        self.check_instance_connectivity(remote, dhcp_namespace, instance_ip)

        self.fuel_web.run_ostf(
            cluster_id=cluster_id,
            test_sets=['ha', 'smoke', 'sanity'])

    @test(depends_on=[deploy_ha_neutron],
          groups=["neutron_l3_migration_after_destroy"])
    @log_snapshot_on_error
    def neutron_l3_migration_after_destroy(self):
        """Check l3-agent rescheduling after destroy non-primary controller

        Scenario:
            1. Revert snapshot with neutron cluster
            2. Manually reschedule router from primary controller
               to another one
            3. Destroy controller with l3-agent
            4. Check l3-agent was rescheduled
            5. Check network connectivity from instance via
               dhcp namespace
            6. Run OSTF

        Duration 30m
        """
        self.env.revert_snapshot("deploy_ha_neutron")
        cluster_id = self.fuel_web.get_last_created_cluster()
        os_conn = os_actions.OpenStackActions(
            self.fuel_web.get_public_vip(cluster_id))

        net_id = os_conn.get_network('net04')['id']
        devops_node = self.get_node_with_dhcp(self, os_conn, net_id)
        remote = self.env.get_ssh_to_remote_by_name(devops_node.name)

        dhcp_namespace = ''.join(remote.execute('ip netns | grep {0}'.format(
            net_id))['stdout']).rstrip()
        logger.debug('dhcp namespace is {0}'.format(dhcp_namespace))

        instance_ip = \
            self.create_instance_with_keypair(
                os_conn, remote).addresses['net04'][0]['addr']
        logger.debug('instance internal ip is {0}'.format(instance_ip))

        router_id = os_conn.get_routers_ids()[0]
        self.reshedule_router_manually(os_conn, router_id)
        self.check_instance_connectivity(remote, dhcp_namespace, instance_ip)

        node_with_l3 = os_conn.get_l3_agent_hosts(router_id)[0]
        new_devops = self.get_node_with_l3(self, node_with_l3)
        new_devops.destroy()
        wait(lambda: not self.fuel_web.get_nailgun_node_by_devops_node(
            new_devops)['online'], timeout=60 * 10)
        self.fuel_web.wait_mysql_galera_is_up(
            [n.name for n in
             set(self.env.get_virtual_environment(
             ).nodes().slaves[:3]) - {new_devops}])

        try:
            wait(lambda: not node_with_l3 == os_conn.get_l3_agent_hosts(
                router_id)[0], timeout=60 * 3)
        except TimeoutError:
            raise TimeoutError(
                "l3 agent wasn't rescheduled, it is still {0}".format(
                    os_conn.get_l3_agent_hosts(router_id)[0]))
        wait(lambda: os_conn.get_l3_agent_ids(router_id), timeout=60)

        self.check_instance_connectivity(remote, dhcp_namespace, instance_ip)

        @retry(count=3, delay=120)
        def run_single_test(cluster_id):
            self.fuel_web.run_single_ostf_test(
                cluster_id, test_sets=['smoke'],
                test_name='fuel_health.tests.smoke.'
                          'test_neutron_actions.TestNeutron.'
                          'test_check_neutron_objects_creation')

        run_single_test(cluster_id)

        self.fuel_web.run_ostf(
            cluster_id=cluster_id,
            test_sets=['ha', 'smoke', 'sanity'],
            should_fail=1,
            failed_test_name=['Check that required services are running'])

    @test(depends_on=[deploy_ha_neutron],
          groups=["neutron_packets_drops_stat"])
    @log_snapshot_on_error
    def neutron_packets_drop_stat(self):
        """Check packets drops statistic when size is equal to MTU

        Scenario:
            1. Revert snapshot with neutron cluster
            2. Create instance, assign floating IP to it
            3. Send ICMP packets from controller to instance with 1500 bytes
            4. If at least 7 responses on 10 requests are received
               assume test is passed

        Duration 30m

        """
        self.env.revert_snapshot("deploy_ha_neutron")
        cluster_id = self.fuel_web.get_last_created_cluster()
        os_conn = os_actions.OpenStackActions(
            self.fuel_web.get_public_vip(cluster_id))

        instance = os_conn.create_server_for_migration(neutron=True)
        floating_ip = os_conn.assign_floating_ip(instance)
        logger.debug("instance floating ip is {0}".format(floating_ip.ip))
        remote = self.env.get_ssh_to_remote_by_name('slave-01')
        mtu_cmd = r"cat /sys/class/net/$(ip r g {0} |" \
                  r" sed -rn" \
                  r" 's/.*dev\s+(\S+)\s.*/\1/p')/mtu".format(floating_ip.ip)
        mtu = ''.join(remote.execute(mtu_cmd)['stdout'])
        logger.debug('mtu is equal to {0}'.format(mtu))
        cmd = "ping -q -s {0} -c 7 -w 10 {1}".format(int(mtu) - 28,
                                                     floating_ip.ip)
        res = remote.execute(cmd)
        assert_equal(0, res['exit_code'],
                     'most packages were dropped, result is {0}'.format(res))
