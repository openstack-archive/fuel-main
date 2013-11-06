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
from devops.helpers.helpers import wait
from proboscis import test, SkipTest
from proboscis.asserts import assert_true, assert_equal

from fuelweb_test.helpers.decorators import debug, log_snapshot_on_error
from fuelweb_test.helpers.eb_tables import Ebtables
from fuelweb_test.models.fuel_web_client import DEPLOYMENT_MODE_SIMPLE
from fuelweb_test.tests.base_test_case import TestBasic, SetupEnvironment

logger = logging.getLogger(__name__)
logwrap = debug(logger)


@test(groups=["thread_2"])
class OneNodeDeploy(TestBasic):

    @test(depends_on=[SetupEnvironment.prepare_release])
    @log_snapshot_on_error
    def deploy_one_node(self):
        self.env.revert_snapshot("ready")
        self.fuel_web.client.get_root()
        self.env.bootstrap_nodes(self.env.nodes().slaves[:1])

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {'slave-01': ['controller']}
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)
        self.fuel_web.assert_cluster_ready(
            'slave-01', smiles_count=4, networks_count=1, timeout=300)


@test(groups=["thread_2"])
class SimpleFlat(TestBasic):

    @test(
        groups=["smoke"],
        depends_on=[SetupEnvironment.prepare_slaves_3])
    @log_snapshot_on_error
    def deploy_simple_flat(self):

        self.check_run("deploy_simple_flat")
        self.env.revert_snapshot("ready_with_3_slaves")

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE_SIMPLE
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['compute']
            }
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)
        self.fuel_web.assert_cluster_ready(
            'slave-01', smiles_count=6, networks_count=1, timeout=300)
        self.env.make_snapshot("deploy_simple_flat")

    @test(groups=["smoke"], depends_on=[deploy_simple_flat])
    @log_snapshot_on_error
    def simple_flat_verify_networks(self):
        self.env.revert_snapshot("deploy_simple_flat")

        #self.env.get_ebtables(self.fuel_web.get_last_created_cluster(),
        #                      self.env.nodes().slaves[:2]).restore_vlans()
        task = self.fuel_web.run_network_verify(
            self.fuel_web.get_last_created_cluster())
        self.fuel_web.assert_task_success(task, 60 * 2, interval=10)

    @test(groups=["smoke"], depends_on=[deploy_simple_flat])
    @log_snapshot_on_error
    def simple_flat_ostf(self):
        self.env.revert_snapshot("deploy_simple_flat")

        self.fuel_web.run_ostf(
            cluster_id=self.fuel_web.get_last_created_cluster(),
            should_fail=5, should_pass=17
        )

    @test(depends_on=[deploy_simple_flat])
    @log_snapshot_on_error
    def simple_flat_network_configuration(self):
        self.env.revert_snapshot("deploy_simple_flat")

        self.env.verify_network_configuration("slave-01")

    @test(depends_on=[deploy_simple_flat])
    @log_snapshot_on_error
    def simple_flat_node_deletion(self):
        self.env.revert_snapshot("deploy_simple_flat")

        cluster_id = self.fuel_web.get_last_created_cluster()
        nailgun_nodes = self.fuel_web.update_nodes(
            cluster_id, {'slave-01': ['controller']}, False, True)
        task = self.fuel_web.deploy_cluster(cluster_id)
        self.fuel_web.assert_task_success(task)
        nodes = filter(lambda x: x["pending_deletion"] is True, nailgun_nodes)
        assert_true(
            len(nodes) == 1, "Verify 1 node has pending deletion status"
        )
        wait(
            lambda: self.fuel_web.is_node_discovered(nodes[0]),
            timeout=3 * 60
        )

    @test(depends_on=[deploy_simple_flat])
    @log_snapshot_on_error
    def simple_flat_blocked_vlan(self):
        self.env.revert_snapshot("deploy_simple_flat")

        cluster_id = self.fuel_web.get_last_created_cluster()
        ebtables = self.env.get_ebtables(
            cluster_id, self.env.nodes().slaves[:2])
        ebtables.restore_vlans()
        try:
            ebtables.block_first_vlan()
            task = self.fuel_web.run_network_verify(cluster_id)
            self.fuel_web.assert_task_failed(task, 60 * 2)
        finally:
            ebtables.restore_first_vlan()

    @test(depends_on=[deploy_simple_flat])
    @log_snapshot_on_error
    def simple_flat_add_compute(self):
        self.env.revert_snapshot("deploy_simple_flat")

        cluster_id = self.fuel_web.get_last_created_cluster()
        self.fuel_web.update_nodes(
            cluster_id, {'slave-03': ['compute']}, True, False)
        self.fuel_web.deploy_cluster_wait(cluster_id)

        assert_equal(
            3, len(self.fuel_web.client.list_cluster_nodes(cluster_id)))

        self.fuel_web.assert_cluster_ready(
            "slave-01", smiles_count=8, networks_count=1, timeout=300)
        self.env.verify_node_service_list("slave-02", 8)
        self.env.verify_node_service_list("slave-03", 8)

        self.env.make_snapshot("simple_flat_add_compute")

    @test(depends_on=[simple_flat_add_compute])
    @log_snapshot_on_error
    def simple_flat_add_compute_ostf(self):
        self.env.revert_snapshot("simple_flat_add_compute")

        self.fuel_web.run_ostf(
            cluster_id=self.fuel_web.get_last_created_cluster(),
            should_fail=5, should_pass=17
        )


@test(groups=["thread_2"])
class SimpleVlan(TestBasic):

    @test(depends_on=[SetupEnvironment.prepare_slaves_3])
    @log_snapshot_on_error
    def deploy_simple_vlan(self):
        self.env.revert_snapshot("ready_with_3_slaves")

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE_SIMPLE
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['compute']
            }
        )
        self.fuel_web.update_vlan_network_fixed(
            cluster_id, amount=8, network_size=32)
        self.fuel_web.deploy_cluster_wait(cluster_id)
        self.fuel_web.assert_cluster_ready(
            'slave-01', smiles_count=6, networks_count=8, timeout=300)
        self.env.make_snapshot("deploy_simple_vlan")

    @test(depends_on=[deploy_simple_vlan])
    @log_snapshot_on_error
    def simple_vlan_verify_networks(self):
        self.env.revert_snapshot("deploy_simple_vlan")

        task = self.fuel_web.run_network_verify(
            self.fuel_web.get_last_created_cluster())
        self.fuel_web.assert_task_success(task, 60 * 2, interval=10)

    @test(depends_on=[deploy_simple_vlan])
    @log_snapshot_on_error
    def simple_vlan_ostf(self):
        self.env.revert_snapshot("deploy_simple_vlan")

        self.fuel_web.run_ostf(
            cluster_id=self.fuel_web.get_last_created_cluster(),
            should_fail=5, should_pass=17
        )


@test(groups=["thread_3", "multirole"])
class MultiroleControllerCinder(TestBasic):

    @test(depends_on=[SetupEnvironment.prepare_slaves_3])
    @log_snapshot_on_error
    def deploy_multirole_controller_cinder(self):
        self.env.revert_snapshot("ready_with_3_slaves")

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE_SIMPLE
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller', 'cinder'],
                'slave-02': ['compute']
            }
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)

        self.env.make_snapshot("deploy_multirole_controller_cinder")

    @test(depends_on=[deploy_multirole_controller_cinder])
    @log_snapshot_on_error
    def deploy_multirole_controller_cinder_verify_networks(self):
        self.env.revert_snapshot("deploy_multirole_controller_cinder")
        self.fuel_web.verify_network(self.fuel_web.get_last_created_cluster())

    @test(depends_on=[deploy_multirole_controller_cinder])
    @log_snapshot_on_error
    def deploy_multirole_controller_cinder_ostf(self):
        self.env.revert_snapshot("deploy_multirole_controller_cinder")

        self.fuel_web.run_ostf(
            cluster_id=self.fuel_web.get_last_created_cluster(),
            should_fail=4, should_pass=19
        )


@test(groups=["thread_3", "multirole"])
class MultiroleComputeCinder(TestBasic):

    @test(depends_on=[SetupEnvironment.prepare_slaves_3])
    @log_snapshot_on_error
    def deploy_multirole_compute_cinder(self):
        self.env.revert_snapshot("ready_with_3_slaves")

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE_SIMPLE
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['compute', 'cinder']
            }
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)

        self.env.make_snapshot("deploy_multirole_compute_cinder")

    @test(depends_on=[deploy_multirole_compute_cinder])
    @log_snapshot_on_error
    def deploy_multirole_compute_cinder_verify_networks(self):
        self.env.revert_snapshot("deploy_multirole_compute_cinder")
        self.fuel_web.verify_network(self.fuel_web.get_last_created_cluster())

    @test(depends_on=[deploy_multirole_compute_cinder])
    @log_snapshot_on_error
    def deploy_multirole_compute_cinder_ostf(self):
        self.env.revert_snapshot("deploy_multirole_compute_cinder")

        self.fuel_web.run_ostf(
            cluster_id=self.fuel_web.get_last_created_cluster(),
            should_fail=4, should_pass=19
        )


@test(groups=["thread_2"])
class UntaggedNetwork(TestBasic):

    @test(depends_on=[SetupEnvironment.prepare_slaves_3])
    @log_snapshot_on_error
    def prepare_untagged_network(self):
        self.env.revert_snapshot("ready_with_3_slaves")

        vlan_turn_off = {'vlan_start': None}
        interfaces = {
            'eth0': ["storage"],
            'eth1': ["public", "floating"],
            'eth2': ["management"],
            'eth3': ["fixed"]
        }

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE_SIMPLE
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['compute']
            }
        )
        nets = self.fuel_web.client.get_networks(cluster_id)['networks']
        nailgun_nodes = self.fuel_web.client.list_cluster_nodes(cluster_id)
        for node in nailgun_nodes:
            self.fuel_web.update_node_networks(node['id'], interfaces)

        # select networks that will be untagged:
        [net.update(vlan_turn_off) for net in nets if net["name"] != "storage"]

        # stop using VLANs:
        self.fuel_web.client.update_network(cluster_id, networks=nets)

        self.env.make_snapshot("prepare_untagged_network")

    @test(depends_on=[prepare_untagged_network])
    @log_snapshot_on_error
    def untagged_network_verify_networks(self):
        self.env.revert_snapshot("prepare_untagged_network")
        self.fuel_web.verify_network(self.fuel_web.get_last_created_cluster())

    @test(depends_on=[prepare_untagged_network])
    @log_snapshot_on_error
    def deploy_untagged_network(self):
        self.env.revert_snapshot("prepare_untagged_network")

        self.fuel_web.deploy_cluster_wait(
            self.fuel_web.get_last_created_cluster())
        self.fuel_web.assert_cluster_ready(
            'slave-01', smiles_count=6, networks_count=1, timeout=300)
        self.env.make_snapshot("deploy_untagged_network")

    @test(depends_on=[deploy_untagged_network])
    @log_snapshot_on_error
    def deploy_untagged_network_verify_networks(self):
        self.env.revert_snapshot("deploy_untagged_network")
        self.fuel_web.verify_network(self.fuel_web.get_last_created_cluster())


@test(groups=["thread_2"])
class FloatingIPs(TestBasic):

    @test(depends_on=[SetupEnvironment.prepare_slaves_3])
    @log_snapshot_on_error
    def deploy_floating_ips(self):
        self.env.revert_snapshot("ready_with_3_slaves")

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE_SIMPLE
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['compute']
            }
        )
        # set ip ranges for floating network
        networks = self.fuel_web.client.get_networks(cluster_id)
        for interface, network in enumerate(networks['networks']):
            if network['name'] == 'floating':
                networks['networks'][interface]['ip_ranges'] = [
                    ['240.0.0.2', '240.0.0.10'],
                    ['240.0.0.20', '240.0.0.25'],
                    ['240.0.0.30', '240.0.0.35']]
                break

        self.fuel_web.client.update_network(
            cluster_id,
            net_manager=networks['net_manager'],
            networks=networks['networks']
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)

        # assert ips
        expected_ips = ['240.0.0.%s' % i for i in range(2, 11, 1)] + \
                       ['240.0.0.%s' % i for i in range(20, 26, 1)] + \
                       ['240.0.0.%s' % i for i in range(30, 36, 1)]
        self.fuel_web.assert_cluster_floating_list('slave-02', expected_ips)

        self.env.make_snapshot("deploy_floating_ips")

    @test(depends_on=[deploy_floating_ips])
    @log_snapshot_on_error
    def deploy_floating_ips_ostf(self):
        self.env.revert_snapshot("deploy_floating_ips")

        self.fuel_web.run_ostf(
            cluster_id=self.fuel_web.get_last_created_cluster(),
            should_fail=5, should_pass=17
        )


@test(groups=["thread_1"])
class SimpleCinder(TestBasic):

    @test(depends_on=[SetupEnvironment.prepare_slaves_3])
    @log_snapshot_on_error
    def deploy_simple_cinder(self):
        self.env.revert_snapshot("ready_with_3_slaves")

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE_SIMPLE
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['compute'],
                'slave-03': ['cinder']
            }
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)
        self.fuel_web.assert_cluster_ready(
            'slave-01', smiles_count=6, networks_count=1, timeout=300)
        self.env.make_snapshot("deploy_simple_cinder")

    @test(depends_on=[deploy_simple_cinder])
    @log_snapshot_on_error
    def simple_cinder_ostf(self):
        self.env.revert_snapshot("deploy_simple_cinder")

        self.fuel_web.run_ostf(
            cluster_id=self.fuel_web.get_last_created_cluster(),
            should_fail=4, should_pass=18
        )


@test(groups=["thread_1"])
class NodeMultipleInterfaces(TestBasic):

    @test(depends_on=[SetupEnvironment.prepare_slaves_3])
    @log_snapshot_on_error
    def deploy_node_multiple_interfaces(self):
        self.env.revert_snapshot("ready_with_3_slaves")

        interfaces_dict = {
            'eth0': ['management'],
            'eth1': ['floating', 'public'],
            'eth2': ['storage'],
            'eth3': ['fixed']
        }

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE_SIMPLE
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['compute'],
                'slave-03': ['cinder']
            }
        )
        nailgun_nodes = self.fuel_web.client.list_cluster_nodes(cluster_id)
        for node in nailgun_nodes:
            self.fuel_web.update_node_networks(node['id'], interfaces_dict)

        self.fuel_web.deploy_cluster_wait(cluster_id)
        for node in ['slave-01', 'slave-02', 'slave-03']:
            self.env.verify_network_configuration(node)

        self.env.make_snapshot("deploy_node_multiple_interfaces")

    @test(depends_on=[deploy_node_multiple_interfaces])
    @log_snapshot_on_error
    def deploy_node_multiple_interfaces_verify_networks(self):
        self.env.revert_snapshot("deploy_node_multiple_interfaces")

        task = self.fuel_web.run_network_verify(
            self.fuel_web.get_last_created_cluster())
        self.fuel_web.assert_task_success(task, 60 * 2, interval=10)


@test(groups=["thread_1"])
class NodeDiskSizes(TestBasic):

    @test(depends_on=[SetupEnvironment.prepare_slaves_3])
    @log_snapshot_on_error
    def check_nodes_notifications(self):
        self.env.revert_snapshot("ready_with_3_slaves")

        # assert /api/nodes
        nailgun_nodes = self.fuel_web.client.list_nodes()
        for node in nailgun_nodes:
            for disk in node['meta']['disks']:
                assert_equal(disk['size'], 21474836480, 'Disk size')

        notifications = self.fuel_web.client.get_notifications()
        for node in nailgun_nodes:
            # assert /api/notifications
            for notification in notifications:
                if notification['node_id'] == node['id']:
                    assert_true('64.0 GB HDD' in notification['message'])

            # assert disks
            disks = self.fuel_web.client.get_node_disks(node['id'])
            for disk in disks:
                assert_equal(disk['size'], 19980, 'Disk size')

    @test(depends_on=[SimpleCinder.deploy_simple_cinder])
    @log_snapshot_on_error
    def check_nodes_disks(self):
        self.env.revert_snapshot("deploy_simple_cinder")

        nodes_dict = {
            'slave-01': ['controller'],
            'slave-02': ['compute'],
            'slave-03': ['cinder']
        }

        # assert node disks after deployment
        for node_name in nodes_dict:
            str_block_devices = self.get_cluster_block_devices(node_name)
            self.assertRegexpMatches(
                str_block_devices,
                'vda\s+\d+:\d+\s+0\s+20G\s+0\s+disk'
            )
            self.assertRegexpMatches(
                str_block_devices,
                'vdb\s+\d+:\d+\s+0\s+20G\s+0\s+disk'
            )
            self.assertRegexpMatches(
                str_block_devices,
                'vdc\s+\d+:\d+\s+0\s+20G\s+0\s+disk'
            )


@test(groups=["thread_2"])
class MultinicBootstrap(TestBasic):

    @test(depends_on=[SetupEnvironment.prepare_release])
    @log_snapshot_on_error
    def multinic_bootstrap_booting(self):
        self.env.revert_snapshot("ready")

        slave = self.env.nodes().slaves[0]
        mac_addresses = [interface.mac_address for interface in
                         slave.interfaces.filter(network__name='internal')]
        try:
            for mac in mac_addresses:
                Ebtables.block_mac(mac)
            for mac in mac_addresses:
                Ebtables.restore_mac(mac)
                slave.destroy(verbose=False)
                self.env.nodes().admins[0].revert("ready")
                nailgun_slave = self.env.bootstrap_nodes([slave])[0]
                assert_equal(mac.upper(), nailgun_slave['mac'].upper())
                Ebtables.block_mac(mac)
        finally:
            for mac in mac_addresses:
                Ebtables.restore_mac(mac)


@test(groups=["thread_2", "test"])
class DeleteEnvironment(TestBasic):

    @test(depends_on=[SimpleFlat.deploy_simple_flat])
    @log_snapshot_on_error
    def delete_environment(self):
        """Delete existing environment
        and verify nodes returns to unallocated state

        Scenario:
            1. Revert snapshot "deploy_simple_flat"
            2. Delete environment
            3. Verify node returns to unallocated pull

        """
        self.env.revert_snapshot("deploy_simple_flat")

        cluster_id = self.fuel_web.get_last_created_cluster()
        self.fuel_web.client.delete_cluster(cluster_id)
        nailgun_nodes = self.fuel_web.client.list_nodes()
        nodes = filter(lambda x: x["pending_deletion"] is True, nailgun_nodes)
        assert_true(
            len(nodes) == 2, "Verify 2 node has pending deletion status"
        )
        wait(
            lambda:
            self.fuel_web.is_node_discovered(nodes[0]) and
            self.fuel_web.is_node_discovered(nodes[1]),
            timeout=3 * 60,
            interval=15
        )


@test(groups=["thread_1"])
class UntaggedNetworksNegative(TestBasic):

    @test(
        depends_on=[SetupEnvironment.prepare_slaves_3],
        enabled=False)
    @log_snapshot_on_error
    def untagged_networks_negative(self):
        self.env.revert_snapshot("ready_with_3_slaves")

        vlan_turn_off = {'vlan_start': None}
        interfaces = {
            'eth0': ["fixed"],
            'eth1': ["public", "floating"],
            'eth2': ["management", "storage"],
            'eth3': []
        }

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['compute']
            }
        )

        nets = self.fuel_web.client.get_networks(cluster_id)['networks']
        nailgun_nodes = self.fuel_web.client.list_cluster_nodes(cluster_id)
        for node in nailgun_nodes:
            self.fuel_web.update_node_networks(node['id'], interfaces)

        # select networks that will be untagged:
        [net.update(vlan_turn_off) for net in nets]

        # stop using VLANs:
        self.fuel_web.client.update_network(cluster_id, networks=nets)

        # run network check:
        task = self.fuel_web.run_network_verify(cluster_id)
        self.fuel_web.assert_task_failed(task, 60 * 5)

        # deploy cluster:
        task = self.fuel_web.deploy_cluster(cluster_id)
        self.fuel_web.assert_task_failed(task)
