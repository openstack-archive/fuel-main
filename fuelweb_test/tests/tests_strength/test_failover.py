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
from proboscis.asserts import assert_not_equal
from proboscis.asserts import assert_true
from proboscis import test

from fuelweb_test.helpers.decorators import log_snapshot_on_error
from fuelweb_test.settings import DEPLOYMENT_MODE_HA
from fuelweb_test.tests.base_test_case import SetupEnvironment
from fuelweb_test.tests.base_test_case import TestBasic


@test(groups=["thread_5", "ha"])
class TestHaFailover(TestBasic):

    @test(depends_on=[SetupEnvironment.prepare_slaves_5],
          groups=["deploy_ha"])
    @log_snapshot_on_error
    def deploy_ha(self):
        """Deploy cluster in HA mode with flat nova-network

        Scenario:
            1. Create cluster
            2. Add 3 nodes with controller roles
            3. Add 2 nodes with compute roles
            4. Deploy the cluster
            8. Make snapshot

        Snapshot deploy_ha

        """
        self.env.revert_snapshot("ready_with_5_slaves")

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE_HA
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
        self.env.make_snapshot("deploy_ha")

    @test(depends_on_groups=['deploy_ha'],
          groups=["ha_destroy_controllers"])
    @log_snapshot_on_error
    def ha_destroy_controllers(self):
        """Destory two controllers and check pacemaker status is correct

        Scenario:
            1. Destroy first controller
            2. Check pacemaker status
            3. Revert environment
            4. Destroy second controller
            5. Check pacemaker status

        Snapshot deploy_ha

        """

        for devops_node in self.env.nodes().slaves[:2]:
            self.env.revert_snapshot("deploy_ha")

            devops_node.suspend(False)
            self.fuel_web.assert_pacemaker(
                self.env.nodes().slaves[2].name,
                set(self.env.nodes().slaves[:3]) - {devops_node},
                [devops_node])

    @test(depends_on_groups=['deploy_ha'],
          groups=["ha_disconnect_controllers"])
    @log_snapshot_on_error
    def ha_disconnect_controllers(self):
        """Disconnect controllers and check pacemaker status is correct

        Scenario:
            1. Disconnect eth3 of the first controller
            2. Check pacemaker status
            3. Revert environment
            4. Disconnect eth3 of the second controller
            5. Check pacemaker status

        Snapshot deploy_ha

        """

        for devops_node in self.env.nodes().slaves[:2]:
            self.env.revert_snapshot("deploy_ha")

            remote = self.fuel_web.get_ssh_for_node(devops_node.name)
            remote.check_call('ifconfig eth2 down')
            self.fuel_web.assert_pacemaker(
                self.env.nodes().slaves[2].name,
                set(self.env.nodes().slaves[:3]) - {devops_node},
                [devops_node])

    @test(depends_on_groups=['deploy_ha'],
          groups=["ha_delete_vips"])
    @log_snapshot_on_error
    def ha_delete_vips(self):
        """Delete all secondary VIPs on all controller nodes.
        Verify that they are restored.
        Verify total amount of secondary IPs. Should be 2:
        management and public

        Scenario:
            1. Delete all secondary VIP
            2. Wait while it is being restored
            3. Verify it is restored

        Snapshot deploy_ha

        """
        self.env.revert_snapshot("deploy_ha")
        cluster_id = \
            self.fuel_web.client.get_cluster_id(self.__class__.__name__)
        interfaces = ('eth1', 'eth2')
        slaves = self.env.nodes().slaves[:3]
        ips_amount = 0
        for devops_node in slaves:
            # Verify VIPs are started.
            ret = self.fuel_web.get_pacemaker_status(devops_node.name)
            assert_true(
                re.search('vip__management_old\s+\(ocf::heartbeat:IPaddr2\):'
                          '\s+Started node', ret), 'vip management started')
            assert_true(
                re.search('vip__public_old\s+\(ocf::heartbeat:IPaddr2\):'
                          '\s+Started node', ret), 'vip public started')

            for interface in interfaces:
                # Look for secondary ip and remove it
                addresses = self.fuel_web.ip_address_show(
                    devops_node.name, interface)
                ip_search = re.search(
                    'inet (?P<ip>\d+\.\d+\.\d+.\d+/\d+) brd '
                    '(?P<mask>\d+\.\d+\.\d+.\d+) scope global '
                    '{0}:ka'.format(interface), addresses)
                if ip_search is None:
                    continue
                ip = ip_search.group('ip')
                self.fuel_web.ip_address_del(
                    devops_node.name, interface, ip)

                # The ip should be restored
                ip_assigned = lambda nodes: \
                    any([ip in self.fuel_web.ip_address_show(
                        n.name, interface, '| grep ka$') for n in nodes])

                wait(lambda: ip_assigned(slaves), timeout=10)
                assert_true(ip_assigned(slaves), 'Secondary IP is restored')
                ips_amount += 1
                # Run OSTF tests
                failed_test_name = ['Create volume and attach it to instance']
                self.fuel_web.run_ostf(
                    cluster_id=cluster_id,
                    test_sets=['ha', 'smoke', 'sanity'],
                    should_fail=1,
                    failed_test_name=failed_test_name)
                # Revert initial state. VIP could be moved to other controller
                self.env.revert_snapshot("deploy_ha")
        assert_equal(ips_amount, 2, 'Secondary IPs amount')

    @test(depends_on_groups=['deploy_ha'],
          groups=["ha_mysql_termination"])
    @log_snapshot_on_error
    def ha_mysql_termination(self):
        """Terminate mysql on all controllers one by one

        Scenario:
            1. Terminate mysql
            2. Wait while it is being restarted
            3. Verify it is restarted
            4. Go to another controller

        Snapshot deploy_ha

        """
        self.env.revert_snapshot("deploy_ha")

        for devops_node in self.env.nodes().slaves[:3]:
            remote = self.fuel_web.get_ssh_for_node(devops_node.name)
            remote.check_call('kill -9 $(pidof -x mysqld_safe)')
            remote.check_call('kill -9 $(pidof mysqld)')

            mysql_started = lambda: \
                len(remote.check_call(
                    'ps aux | grep "/usr/sbin/mysql"')['stdout']) == 3
            wait(mysql_started, timeout=300)
            assert_true(mysql_started(), 'MySQL restarted')

    @test(depends_on_groups=['deploy_ha'],
          groups=["ha_haproxy_termination"])
    @log_snapshot_on_error
    def ha_haproxy_termination(self):
        """Terminate haproxy on all controllers one by one

        Scenario:
            1. Terminate haproxy
            2. Wait while it is being restarted
            3. Verify it is restarted
            4. Go to another controller

        Snapshot deploy_ha

        """
        self.env.revert_snapshot("deploy_ha")

        for devops_node in self.env.nodes().slaves[:3]:
            remote = self.fuel_web.get_ssh_for_node(devops_node.name)
            remote.check_call('kill -9 $(pidof haproxy)')

            mysql_started = lambda: \
                len(remote.check_call(
                    'ps aux | grep "/usr/sbin/haproxy"')['stdout']) == 3
            wait(mysql_started, timeout=20)
            assert_true(mysql_started(), 'haproxy restarted')

    @test(depends_on_groups=['deploy_ha'],
          groups=["ha_pacemaker_configuration"])
    @log_snapshot_on_error
    def ha_pacemaker_configuration(self):
        """Verify resources are configured

        Scenario:
            1. SSH to controller node
            2. Verify resources are configured
            3. Go to next controller

        Snapshot deploy_ha

        """
        self.env.revert_snapshot("deploy_ha")

        devops_ctrls = self.env.nodes().slaves[:3]
        for devops_node in devops_ctrls:
            config = self.fuel_web.get_pacemaker_config(devops_node.name)
            for n in devops_ctrls:
                fqdn = self.fuel_web.fqdn(n)
                assert_true(
                    'node {0}'.format(fqdn) in config,
                    'node {0} exists'.format(fqdn))
            assert_not_equal(
                re.search('primitive (openstack-)?heat-engine', config), None,
                'heat engine')
            assert_true('primitive p_haproxy' in config, 'haproxy')
            assert_true('primitive p_mysql' in config, 'mysql')
            assert_true(
                'primitive vip__management_old' in config, 'vip management')
            assert_true(
                'primitive vip__public_old' in config, 'vip public')
