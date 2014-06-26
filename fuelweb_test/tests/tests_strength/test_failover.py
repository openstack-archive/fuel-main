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
import time

from devops.helpers.helpers import wait
from proboscis.asserts import assert_equal
from proboscis.asserts import assert_not_equal
from proboscis.asserts import assert_true
from proboscis import test

from fuelweb_test.helpers.decorators import log_snapshot_on_error
from fuelweb_test import logger
from fuelweb_test.settings import DEPLOYMENT_MODE_HA
from fuelweb_test.settings import NEUTRON_SEGMENT_TYPE
from fuelweb_test.settings import NEUTRON_FAILOVER
from fuelweb_test.tests.base_test_case import SetupEnvironment
from fuelweb_test.tests.base_test_case import TestBasic


@test(groups=["thread_5", "ha", "neutron_failover"])
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

        settings = None

        if NEUTRON_FAILOVER:
            settings = {
                "net_provider": 'neutron',
                "net_segment_type": NEUTRON_SEGMENT_TYPE
            }
        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE_HA,
            settings=settings
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
        self.env.make_snapshot("deploy_ha", is_make=True)

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
            6. Run OSTF

        Snapshot deploy_ha

        """

        for devops_node in self.env.nodes().slaves[:2]:
            self.env.revert_snapshot("deploy_ha")

            devops_node.suspend(False)
            self.fuel_web.assert_pacemaker(
                self.env.nodes().slaves[2].name,
                set(self.env.nodes().slaves[:3]) - {devops_node},
                [devops_node])

        cluster_id = self.fuel_web.client.get_cluster_id(
            self.__class__.__name__)

        self.fuel_web.run_ostf(
            cluster_id=cluster_id,
            test_sets=['ha', 'smoke', 'sanity'],
            should_fail=3,
            failed_test_name=['Create volume and boot instance from it',
                              'Create volume and attach it to instance'])

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
            6. Run OSTF

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

        cluster_id = self.fuel_web.client.get_cluster_id(
            self.__class__.__name__)

        self.fuel_web.run_ostf(
            cluster_id=cluster_id,
            test_sets=['ha', 'smoke', 'sanity'],
            should_fail=2,
            failed_test_name=['Create volume and boot instance from it',
                              'Create volume and attach it to instance'])

    @test(depends_on_groups=['deploy_ha'],
          groups=["ha_delete_vips"])
    @log_snapshot_on_error
    def ha_delete_vips(self):
        """Delete all management and public VIPs on all controller nodes.
        Verify that they are restored.
        Verify total amount of secondary IPs. Should be 2:
        management and public

        Scenario:
            1. Delete all secondary VIP
            2. Wait while it is being restored
            3. Verify it is restored
            4. Run OSTF

        Snapshot deploy_ha

        """
        logger.debug('Start reverting of deploy_ha snapshot')
        self.env.revert_snapshot("deploy_ha")
        cluster_id = \
            self.fuel_web.client.get_cluster_id(self.__class__.__name__)
        logger.debug('Cluster id is {0}'.format(cluster_id))
        interfaces = ('hapr-p', 'hapr-m')
        slaves = self.env.nodes().slaves[:3]
        logger.debug("Current nodes are {0}".format([i.name for i in slaves]))
        ips_amount = 0
        for devops_node in slaves:
            # Verify VIPs are started.
            ret = self.fuel_web.get_pacemaker_status(devops_node.name)
            logger.debug("Pacemaker status {0} for node {1}".format
                         (ret, devops_node.name))
            assert_true(
                re.search('vip__management_old\s+\(ocf::mirantis:ns_IPaddr2\):'
                          '\s+Started node', ret),
                'vip management not started. '
                'Current pacemaker status is {0}'.format(ret))
            assert_true(
                re.search('vip__public_old\s+\(ocf::mirantis:ns_IPaddr2\):'
                          '\s+Started node', ret),
                'vip public not started. '
                'Current pacemaker status is {0}'.format(ret))

            for interface in interfaces:
                # Look for management and public ip in namespace and remove it
                logger.debug("Start to looking for ip of Vips")
                addresses = self.fuel_web.ip_address_show(
                    devops_node.name, interface=interface,
                    namespace='haproxy',
                    pipe_str='| grep {0}$'.format(interface))
                logger.debug("Vip addresses is {0} for node {1} and interface"
                             " {2}".format(addresses, devops_node.name,
                                           interface))
                ip_search = re.search(
                    'inet (?P<ip>\d+\.\d+\.\d+.\d+/\d+) scope global '
                    '{0}'.format(interface), addresses)

                if ip_search is None:
                    logger.debug("Ip show output does not"
                                 " match in regex. Current value is None")
                    continue
                ip = ip_search.group('ip')
                logger.debug("Founded ip is {0}".format(ip))
                logger.debug("Start ip {0} deletion on node {1} and "
                             "interface {2} ".format(ip, devops_node.name,
                                                     interface))
                self.fuel_web.ip_address_del(
                    node_name=devops_node.name,
                    interface=interface,
                    ip=ip, namespace='haproxy')

                # The ip should be restored
                ip_assigned = lambda nodes: \
                    any([ip in self.fuel_web.ip_address_show(
                        n.name, 'haproxy',
                        interface, '| grep {0}$'.format(interface))
                        for n in nodes])
                logger.debug("Waiting while deleted ip restores ...")
                wait(lambda: ip_assigned(slaves), timeout=30)
                assert_true(ip_assigned(slaves),
                            "IP isn't restored restored.")
                ips_amount += 1

                time.sleep(60)

                # Run OSTF tests
                failed_test_name = ['Create volume and boot instance from it',
                                    'Create volume and attach it to instance']
                self.fuel_web.run_ostf(
                    cluster_id=cluster_id,
                    test_sets=['ha', 'smoke', 'sanity'],
                    should_fail=3,
                    failed_test_name=failed_test_name)
                # Revert initial state. VIP could be moved to other controller
                self.env.revert_snapshot("deploy_ha")
        assert_equal(ips_amount, 2,
                     'Not all vips were recovered after fail in 10s')

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
            5. Run OSTF

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

        cluster_id = self.fuel_web.client.get_cluster_id(
            self.__class__.__name__)

        self.fuel_web.run_ostf(
            cluster_id=cluster_id,
            test_sets=['ha', 'smoke', 'sanity'],
            should_fail=2,
            failed_test_name=['Create volume and boot instance from it',
                              'Create volume and attach it to instance'])

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
            5. Run OSTF

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

        cluster_id = self.fuel_web.client.get_cluster_id(
            self.__class__.__name__)

        self.fuel_web.run_ostf(
            cluster_id=cluster_id,
            test_sets=['ha', 'smoke', 'sanity'],
            should_fail=2,
            failed_test_name=['Create volume and boot instance from it',
                              'Create volume and attach it to instance'])

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
