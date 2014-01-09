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
import re
from devops.error import DevopsCalledProcessError
from devops.helpers.helpers import wait
from proboscis import test
from proboscis.asserts import assert_true, assert_equal

from fuelweb_test.helpers.decorators import debug, log_snapshot_on_error
from fuelweb_test.settings import DEPLOYMENT_MODE_HA
from fuelweb_test.tests.base_test_case import TestBasic, SetupEnvironment

logger = logging.getLogger(__name__)
logwrap = debug(logger)


@test(groups=["thread_3", "ha"])
class TestHaVLAN(TestBasic):

    @test(depends_on=[SetupEnvironment.prepare_slaves_5],
          groups=["deploy_ha_vlan"])
    @log_snapshot_on_error
    def deploy_ha_vlan(self):
        """Deploy cluster in HA mode with VLAN Manager

        Scenario:
            1. Create cluster
            2. Add 3 nodes with controller roles
            3. Add 2 nodes with compute roles
            4. Set up cluster to use Network VLAN manager with 8 networks
            5. Deploy the cluster
            6. Validate cluster was set up correctly, there are no dead
            services, there are no errors in logs
            7. Run network verification
            8. Run OSTF
            9. Create snapshot

        Snapshot deploy_ha_vlan

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
        self.fuel_web.update_vlan_network_fixed(
            cluster_id, amount=8, network_size=32
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)
        self.fuel_web.assert_cluster_ready(
            'slave-01', smiles_count=16, networks_count=8, timeout=300)

        self.fuel_web.verify_network(cluster_id)

        self.fuel_web.run_ostf(
            cluster_id=cluster_id,
            test_sets=['ha', 'smoke', 'sanity'],
            should_fail=4)

        self.env.make_snapshot("deploy_ha_vlan")


@test(groups=["thread_4", "ha"])
class TestHaFlat(TestBasic):

    @test(depends_on=[SetupEnvironment.prepare_slaves_5],
          groups=["deploy_ha_flat"])
    @log_snapshot_on_error
    def deploy_ha_flat(self):
        """Deploy cluster in HA mode with flat nova-network

        Scenario:
            1. Create cluster
            2. Add 3 nodes with controller roles
            3. Add 2 nodes with compute roles
            4. Deploy the cluster
            5. Validate cluster was set up correctly, there are no dead
            services, there are no errors in logs
            6. Run verify networks
            7. Run OSTF
            8. Make snapshot

        Snapshot deploy_ha_flat

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
        self.fuel_web.assert_cluster_ready(
            'slave-01', smiles_count=16, networks_count=1, timeout=300)

        self.fuel_web.verify_network(cluster_id)

        self.fuel_web.run_ostf(
            cluster_id=cluster_id,
            test_sets=['ha', 'smoke', 'sanity'],
            should_fail=4)

        self.env.make_snapshot("deploy_ha_flat")

    @test(depends_on_groups=['deploy_ha_flat'],
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

        Snapshot deploy_ha_flat

        """

        for devops_node in self.env.nodes().slaves[:2]:
            self.env.revert_snapshot("deploy_ha_flat")

            devops_node.suspend(False)
            self.fuel_web.assert_pacemaker(
                self.env.nodes().slaves[2].name,
                set(self.env.nodes().slaves[:3]) - {devops_node},
                [devops_node])

    @test(depends_on_groups=['deploy_ha_flat'],
          groups=["ha_disconnect_controllers"])
    @log_snapshot_on_error
    def ha_disconnect_controllers(self):
        """Destory two controllers and check pacemaker status is correct

        Scenario:
            1. Disconnect eth3 of the first controller
            2. Check pacemaker status
            3. Revert environment
            4. Disconnect eth3 of the second controller
            5. Check pacemaker status

        Snapshot deploy_ha_flat

        """

        for devops_node in self.env.nodes().slaves[:2]:
            self.env.revert_snapshot("deploy_ha_flat")

            remote = self.fuel_web.get_ssh_for_node(devops_node.name)
            remote.check_call('/etc/sysconfig/network-scripts/ifdown '
                              '/etc/sysconfig/network-scripts/ifcfg-eth3')
            self.fuel_web.assert_pacemaker(
                self.env.nodes().slaves[2].name,
                set(self.env.nodes().slaves[:3]) - {devops_node},
                [devops_node])

    @test(depends_on_groups=['deploy_ha_flat'],
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

        Snapshot deploy_ha_flat

        """
        self.env.revert_snapshot("deploy_ha_flat")

        # Verify VIPs are started.
        ret = self.fuel_web.get_pacemaker_status(
            self.env.nodes().slaves[0].name)
        assert_true(
            re.search('vip__management_old\s+\(ocf::heartbeat:IPaddr2\):'
                      '\s+Started node', ret), 'vip management started')
        assert_true(
            re.search('vip__public_old\s+\(ocf::heartbeat:IPaddr2\):'
                      '\s+Started node', ret), 'vip public started')

        interfaces = ('eth1', 'eth3.101')
        ips_amount = 0
        for devops_node in self.env.nodes().slaves[:3]:
            remote = self.fuel_web.get_ssh_for_node(devops_node.name)
            for interface in interfaces:
                try:
                    # Look for secondary ip and remove it
                    ret = remote.check_call(
                        'ip address show {0} | grep ka$'.format(interface))
                    ip = re.search(
                        'inet (?P<ip>.*) brd', ret['stdout'][0]).group('ip')
                    remote.check_call(
                        'ip addr del {0} dev {1}'.format(ip, interface))

                    # The ip should be restored
                    ip_assigned = lambda: ip in ''.join(
                        remote.check_call('ip address show {0}'.format(
                            interface))['stdout'])
                    wait(ip_assigned, timeout=10)
                    assert_true(ip_assigned(),
                                'Secondary IP is restored')
                    ips_amount += 1
                except DevopsCalledProcessError:
                    pass
        assert_equal(ips_amount, 2, 'Secondary IPs amount')

    @test(depends_on_groups=['deploy_ha_flat'],
          groups=["ha_mysql_termination"])
    @log_snapshot_on_error
    def ha_mysql_termination(self):
        """Terminate mysql on all controllers one by one

        Scenario:
            1. Terminate mysql
            2. Wait while it is being restarted
            3. Verify it is restarted
            4. Go to another controller

        Snapshot deploy_ha_flat

        """
        self.env.revert_snapshot("deploy_ha_flat")

        for devops_node in self.env.nodes().slaves[:3]:
            remote = self.fuel_web.get_ssh_for_node(devops_node.name)
            remote.check_call('kill -9 $(pidof mysqld)')

            mysql_started = lambda: \
                len(remote.check_call(
                    'ps aux | grep "/usr/sbin/mysql"')['stdout']) == 3
            wait(mysql_started, timeout=300)
            assert_true(mysql_started(), 'MySQL restarted')

    @test(depends_on_groups=['deploy_ha_flat'],
          groups=["ha_haproxy_termination"])
    @log_snapshot_on_error
    def ha_haproxy_termination(self):
        """Terminate haproxy on all controllers one by one

        Scenario:
            1. Terminate haproxy
            2. Wait while it is being restarted
            3. Verify it is restarted
            4. Go to another controller

        Snapshot deploy_ha_flat

        """
        self.env.revert_snapshot("deploy_ha_flat")

        for devops_node in self.env.nodes().slaves[:3]:
            remote = self.fuel_web.get_ssh_for_node(devops_node.name)
            remote.check_call('kill -9 $(pidof haproxy)')

            mysql_started = lambda: \
                len(remote.check_call(
                    'ps aux | grep "/usr/sbin/haproxy"')['stdout']) == 3
            wait(mysql_started, timeout=20)
            assert_true(mysql_started(), 'haproxy restarted')

    @test(depends_on_groups=['deploy_ha_flat'],
          groups=["ha_pacemaker_configuration"])
    @log_snapshot_on_error
    def ha_pacemaker_configuration(self):
        """Verify resources are configured

        Scenario:
            1. SSH to controller node
            2. Verify resources are configured
            3. Go to next controller

        Snapshot deploy_ha_flat

        """
        self.env.revert_snapshot("deploy_ha_flat")

        devops_ctrls = self.env.nodes().slaves[:3]
        nailgun_ctrls = \
            [self.fuel_web.get_nailgun_node_by_devops_node(n)
             for n in devops_ctrls]

        for devops_node in devops_ctrls:
            config = self.fuel_web.get_pacemaker_config(devops_node.name)
            for n in nailgun_ctrls:
                assert_true(
                    'node {0}'.format(n['fqdn']) in config,
                    'node {0} exists'.format(n['fqdn']))
            assert_true(
                'primitive openstack-heat-engine' in config, 'heat engine')
            assert_true('primitive p_haproxy' in config, 'haproxy')
            assert_true('primitive p_mysql' in config, 'mysql')
            assert_true(
                'primitive vip__management_old' in config, 'vip management')
            assert_true(
                'primitive vip__public_old' in config, 'vip public')


@test(groups=["thread_4", "ha"])
class TestHaFlatAddCompute(TestBasic):

    @test(depends_on=[SetupEnvironment.prepare_slaves_5],
          groups=["ha_flat_add_compute"])
    @log_snapshot_on_error
    def ha_flat_add_compute(self):
        """Add compute node to cluster in HA mode with flat nova-network

        Scenario:
            1. Create cluster
            2. Add 3 nodes with controller roles
            3. Add 2 nodes with compute roles
            4. Deploy the cluster
            5. Validate cluster was set up correctly, there are no dead
            services, there are no errors in logs
            6. Add 1 node with compute role
            7. Deploy the cluster
            8. Run network verification
            9. Run OSTF

        Snapshot ha_flat_add_compute

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
        self.fuel_web.assert_cluster_ready(
            'slave-01', smiles_count=16, networks_count=1, timeout=300)

        self.env.bootstrap_nodes(self.env.nodes().slaves[5:6])
        self.fuel_web.update_nodes(
            cluster_id, {'slave-06': ['compute']}, True, False
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)

        self.fuel_web.verify_network(cluster_id)

        self.fuel_web.run_ostf(
            cluster_id=cluster_id,
            test_sets=['ha', 'smoke', 'sanity'], should_fail=4)

        self.env.make_snapshot("ha_flat_add_compute")
