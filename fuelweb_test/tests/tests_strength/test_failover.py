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
from devops.helpers.helpers import _wait
from proboscis.asserts import assert_equal
from proboscis.asserts import assert_not_equal
from proboscis.asserts import assert_true
from proboscis import test
from proboscis import SkipTest

from fuelweb_test.helpers.checkers import check_mysql
from fuelweb_test.helpers.decorators import log_snapshot_on_error
from fuelweb_test.helpers import os_actions
from fuelweb_test import logger
from fuelweb_test.settings import DEPLOYMENT_MODE
from fuelweb_test.settings import NEUTRON_SEGMENT_TYPE
from fuelweb_test.settings import NEUTRON_ENABLE
from fuelweb_test.tests.base_test_case import SetupEnvironment
from fuelweb_test.tests.base_test_case import TestBasic


@test(groups=["thread_5", "ha", "neutron_failover", "ha_nova_destructive",
              "ha_neutron_destructive"])
class TestHaFailover(TestBasic):

    @test(depends_on=[SetupEnvironment.prepare_slaves_5],
          groups=["deploy_ha"])
    @log_snapshot_on_error
    def deploy_ha(self):
        """Prepare cluster in HA mode for failover tests

        Scenario:
            1. Create cluster
            2. Add 3 nodes with controller roles
            3. Add 2 nodes with compute roles
            4. Deploy the cluster
            8. Make snapshot

        Duration 70m
        Snapshot deploy_ha

        """
        try:
            self.check_run("deploy_ha")
        except SkipTest:
            return

        self.env.revert_snapshot("ready_with_5_slaves")

        settings = None

        if NEUTRON_ENABLE:
            settings = {
                "net_provider": 'neutron',
                "net_segment_type": NEUTRON_SEGMENT_TYPE
            }
        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE,
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
        public_vip = self.fuel_web.get_public_vip(cluster_id)
        os_conn = os_actions.OpenStackActions(public_vip)
        if NEUTRON_ENABLE:
            self.fuel_web.assert_cluster_ready(
                os_conn, smiles_count=14, networks_count=2, timeout=300)
        else:
            self.fuel_web.assert_cluster_ready(
                os_conn, smiles_count=16, networks_count=1, timeout=300)
        self.fuel_web.verify_network(cluster_id)

        self.fuel_web.security.verify_firewall(cluster_id)

        # Bug #1289297. Pause 5 min to make sure that all remain activity
        # on the admin node has over before creating a snapshot.
        time.sleep(5 * 60)

        self.env.make_snapshot("deploy_ha", is_make=True)

    @test(depends_on_groups=['deploy_ha'],
          groups=["ha_destroy_controllers"])
    @log_snapshot_on_error
    def ha_destroy_controllers(self):
        """Destroy two controllers and check pacemaker status is correct

        Scenario:
            1. Destroy first controller
            2. Check pacemaker status
            3. Run OSTF
            4. Revert environment
            5. Destroy second controller
            6. Check pacemaker status
            7. Run OSTF

        Duration 35m
        """

        for devops_node in self.env.get_virtual_environment(
        ).nodes().slaves[:2]:
            self.env.revert_snapshot("deploy_ha")
            devops_node.suspend(False)
            self.fuel_web.assert_pacemaker(
                self.env.get_virtual_environment().nodes(
                ).slaves[2].name,
                set(self.env.get_virtual_environment(
                ).nodes().slaves[:3]) - {devops_node},
                [devops_node])

            cluster_id = self.fuel_web.client.get_cluster_id(
                self.__class__.__name__)

            # Wait until Nailgun marked suspended controller as offline
            wait(lambda: not self.fuel_web.get_nailgun_node_by_devops_node(
                devops_node)['online'],
                timeout=60 * 5)

            # Wait until MySQL Galera is UP on online controllers
            self.fuel_web.wait_mysql_galera_is_up(
                [n.name for n in
                 set(self.env.get_virtual_environment(
                 ).nodes().slaves[:3]) - {devops_node}])

            self.fuel_web.run_ostf(
                cluster_id=cluster_id,
                test_sets=['ha', 'smoke', 'sanity'],
                should_fail=1)

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

        Duration 45m

        """

        for devops_node in self.env.get_virtual_environment(
        ).nodes().slaves[:2]:
            self.env.revert_snapshot("deploy_ha")

            remote = self.fuel_web.get_ssh_for_node(devops_node.name)
            remote.check_call('ifconfig eth2 down')
            self.fuel_web.assert_pacemaker(
                self.env.get_virtual_environment(
                ).nodes().slaves[2].name,
                set(self.env.get_virtual_environment(
                ).nodes().slaves[:3]) - {devops_node},
                [devops_node])

        cluster_id = self.fuel_web.client.get_cluster_id(
            self.__class__.__name__)

        # Wait until MySQL Galera is UP on some controller
        self.fuel_web.wait_mysql_galera_is_up(['slave-01'])

        self.fuel_web.run_ostf(
            cluster_id=cluster_id,
            test_sets=['ha', 'smoke', 'sanity'])

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

        Duration 30m

        """
        logger.debug('Start reverting of deploy_ha snapshot')
        self.env.revert_snapshot("deploy_ha")
        cluster_id = \
            self.fuel_web.client.get_cluster_id(self.__class__.__name__)
        logger.debug('Cluster id is {0}'.format(cluster_id))
        interfaces = ('hapr-p', 'hapr-m')
        slaves = self.env.get_virtual_environment(
        ).nodes().slaves[:3]
        logger.debug("Current nodes are {0}".format([i.name for i in slaves]))
        ips_amount = 0
        for devops_node in slaves:
            # Verify VIPs are started.
            ret = self.fuel_web.get_pacemaker_status(devops_node.name)
            logger.debug("Pacemaker status {0} for node {1}".format
                         (ret, devops_node.name))
            assert_true(
                re.search('vip__management\s+\(ocf::fuel:ns_IPaddr2\):'
                          '\s+Started node', ret),
                'vip management not started. '
                'Current pacemaker status is {0}'.format(ret))
            assert_true(
                re.search('vip__public\s+\(ocf::fuel:ns_IPaddr2\):'
                          '\s+Started node', ret),
                'vip public not started. '
                'Current pacemaker status is {0}'.format(ret))

            for interface in interfaces:
                # Look for management and public ip in namespace and remove it
                logger.debug("Start to looking for ip of Vips")
                addresses = self.fuel_web.ip_address_show(devops_node.name,
                                                          interface=interface,
                                                          namespace='haproxy')
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
                        n.name, 'haproxy', interface)
                        for n in nodes])
                logger.debug("Waiting while deleted ip restores ...")
                wait(lambda: ip_assigned(slaves), timeout=30)
                assert_true(ip_assigned(slaves),
                            "IP isn't restored restored.")
                ips_amount += 1

                time.sleep(60)

                # Run OSTF tests
                self.fuel_web.run_ostf(
                    cluster_id=cluster_id,
                    test_sets=['ha', 'smoke', 'sanity'],
                    should_fail=1)
                # Revert initial state. VIP could be moved to other controller
                self.env.revert_snapshot("deploy_ha")
        assert_equal(ips_amount, 2,
                     'Not all VIPs were found: expect - 2, found {0}'.format(
                         ips_amount))

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

        Duration 15m

        """
        self.env.revert_snapshot("deploy_ha")

        for devops_node in self.env.get_virtual_environment(
        ).nodes().slaves[:3]:
            remote = self.fuel_web.get_ssh_for_node(devops_node.name)
            logger.info('Terminating MySQL on {0}'.format(devops_node.name))

            try:
                remote.check_call('pkill -9 -x "mysqld"')
            except:
                logger.error('MySQL on {0} is down after snapshot revert'.
                             format(devops_node.name))
                raise

            check_mysql(remote, devops_node.name)

        cluster_id = self.fuel_web.client.get_cluster_id(
            self.__class__.__name__)

        self.fuel_web.wait_mysql_galera_is_up(['slave-01', 'slave-02',
                                               'slave-03'])

        self.fuel_web.run_ostf(
            cluster_id=cluster_id,
            test_sets=['ha', 'smoke', 'sanity'])

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

        Duration 25m

        """
        self.env.revert_snapshot("deploy_ha")

        for devops_node in self.env.get_virtual_environment(
        ).nodes().slaves[:3]:
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
            test_sets=['ha', 'smoke', 'sanity'])

    @test(depends_on_groups=['deploy_ha'],
          groups=["ha_pacemaker_configuration"])
    @log_snapshot_on_error
    def ha_pacemaker_configuration(self):
        """Verify resources are configured

        Scenario:
            1. SSH to controller node
            2. Verify resources are configured
            3. Go to next controller

        Duration 15m

        """
        self.env.revert_snapshot("deploy_ha")

        devops_ctrls = self.env.get_virtual_environment(
        ).nodes().slaves[:3]
        pcm_nodes = ' '.join(self.fuel_web.get_pcm_nodes(
            self.env.get_virtual_environment(
            ).nodes().slaves[0].name, pure=True)['Online'])
        logger.debug("pacemaker nodes are {0}".format(pcm_nodes))
        for devops_node in devops_ctrls:
            config = self.fuel_web.get_pacemaker_config(devops_node.name)
            logger.debug("config on node {0} is {1}".format(
                devops_node.name, config))
            assert_not_equal(re.search(
                "vip__public\s+\(ocf::fuel:ns_IPaddr2\):\s+Started\s+"
                "Clone Set:\s+clone_ping_vip__public\s+\[ping_vip__public\]"
                "\s+Started:\s+\[ {0} \]".format(pcm_nodes), config), None,
                'public vip is not configured right')
            assert_true(
                'vip__management	(ocf::fuel:ns_IPaddr2):	Started'
                in config, 'vip management is not configured right')
            assert_not_equal(re.search(
                "Clone Set: clone_p_(heat|openstack-heat)-engine"
                " \[p_(heat|openstack-heat)-engine\]\s+"
                "Started: \[ {0} \]".format(
                    pcm_nodes), config), None,
                'heat engine is not configured right')
            assert_not_equal(re.search(
                "Clone Set: clone_p_mysql \[p_mysql\]\s+Started:"
                " \[ {0} \]".format(pcm_nodes), config), None,
                'mysql is not configured right')
            assert_not_equal(re.search(
                "Clone Set: clone_p_haproxy \[p_haproxy\]\s+Started:"
                " \[ {0} \]".format(pcm_nodes), config), None,
                'haproxy is not configured right')

    @test(enabled=False, depends_on_groups=['deploy_ha'],
          groups=["ha_pacemaker_restart_heat_engine"])
    @log_snapshot_on_error
    def ha_pacemaker_restart_heat_engine(self):
        """Verify heat engine service is restarted
         by pacemaker on amqp connection loss

        Scenario:
            1. SSH to any controller
            2. Check heat-engine status
            3. Block heat-engine amqp connections
            4. Check heat-engine was stopped on current controller
            5. Unblock heat-engine amqp connections
            6. Check heat-engine process is running with new pid
            7. Check amqp connection re-appears for heat-engine

        Duration 15m

        """
        self.env.revert_snapshot("deploy_ha")
        ocf_success = "DEBUG: OpenStack Orchestration Engine" \
                      " (heat-engine) monitor succeeded"
        ocf_error = "ERROR: OpenStack Heat Engine is not connected to the" \
                    " AMQP server: AMQP connection test returned 1"

        heat_name = 'heat-engine'

        ocf_status = \
            'script -q -c "OCF_ROOT=/usr/lib/ocf' \
            ' /usr/lib/ocf/resource.d/fuel/{0}' \
            ' monitor 2>&1"'.format(heat_name)

        remote = self.fuel_web.get_ssh_for_node(
            self.env.get_virtual_environment(
            ).nodes().slaves[0].name)
        pid = ''.join(remote.execute('pgrep heat-engine')['stdout'])
        get_ocf_status = ''.join(
            remote.execute(ocf_status)['stdout']).rstrip()
        assert_true(ocf_success in get_ocf_status,
                    "heat engine is not succeeded, status is {0}".format(
                        get_ocf_status))
        assert_true(len(remote.execute(
            "netstat -nap | grep {0} | grep :5673".
            format(pid))['stdout']) > 0, 'There is no amqp connections')
        remote.execute("iptables -I OUTPUT 1 -m owner --uid-owner heat -m"
                       " state --state NEW,ESTABLISHED,RELATED -j DROP")

        wait(lambda: len(remote.execute
            ("netstat -nap | grep {0} | grep :5673".
             format(pid))['stdout']) == 0, timeout=300)

        get_ocf_status = ''.join(
            remote.execute(ocf_status)['stdout']).rstrip()
        logger.info('ocf status after blocking is {0}'.format(
            get_ocf_status))
        assert_true(ocf_error in get_ocf_status,
                    "heat engine is running, status is {0}".format(
                        get_ocf_status))

        remote.execute("iptables -D OUTPUT 1 -m owner --uid-owner heat -m"
                       " state --state NEW,ESTABLISHED,RELATED")
        _wait(lambda: assert_true(ocf_success in ''.join(
            remote.execute(ocf_status)['stdout']).rstrip()), timeout=240)
        newpid = ''.join(remote.execute('pgrep heat-engine')['stdout'])
        assert_true(pid != newpid, "heat pid is still the same")
        get_ocf_status = ''.join(remote.execute(
            ocf_status)['stdout']).rstrip()
        assert_true(ocf_success in get_ocf_status,
                    "heat engine is not succeeded, status is {0}".format(
                        get_ocf_status))
        assert_true(len(
            remote.execute("netstat -nap | grep {0} | grep :5673".format(
                newpid))['stdout']) > 0)
        cluster_id = self.fuel_web.get_last_created_cluster()
        self.fuel_web.run_ostf(cluster_id=cluster_id)

    @test(depends_on_groups=['deploy_ha'],
          groups=["ha_check_monit"])
    @log_snapshot_on_error
    def ha_check_monit(self):
        """Verify monit restarted nova
         service if it was killed

        Scenario:
            1. SSH to every compute node in cluster
            2. Kill nova-compute service
            3. Check service is restarted by monit

        Duration 25m

        """
        self.env.revert_snapshot("deploy_ha")
        for devops_node in self.env.get_virtual_environment(
        ).nodes().slaves[3:5]:
            remote = self.fuel_web.get_ssh_for_node(devops_node.name)
            remote.execute("kill -9 `pgrep nova-compute`")
            wait(
                lambda: len(remote.execute('pgrep nova-compute')['stdout'])
                == 1, timeout=120)
            assert_true(len(remote.execute('pgrep nova-compute')['stdout'])
                        == 1, 'Nova service was not restarted')
            assert_true(len(remote.execute(
                "grep \"nova-compute.*trying to restart\" "
                "/var/log/monit.log")['stdout']) > 0,
                'Nova service was not restarted')
