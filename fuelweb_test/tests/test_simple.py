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
from proboscis.asserts import assert_true
from proboscis import test

from fuelweb_test.helpers.decorators import log_snapshot_on_error
from fuelweb_test.helpers.eb_tables import Ebtables
from fuelweb_test.settings import DEPLOYMENT_MODE_SIMPLE
from fuelweb_test.settings import NODE_VOLUME_SIZE
from fuelweb_test.tests.base_test_case import SetupEnvironment
from fuelweb_test.tests.base_test_case import TestBasic
from fuelweb_test import logger


@test(groups=["thread_2"])
class OneNodeDeploy(TestBasic):
    @test(depends_on=[SetupEnvironment.prepare_release],
          groups=["deploy_one_node"])
    @log_snapshot_on_error
    def deploy_one_node(self):
        """Deploy cluster with controller node only

        Scenario:
            1. Create cluster
            2. Add 1 node with controller role
            3. Deploy the cluster
            4. Validate cluster was set up correctly, there are no dead
            services, there are no errors in logs

        """
        self.env.revert_snapshot("ready")
        self.fuel_web.client.get_root()
        self.env.bootstrap_nodes(self.env.nodes().slaves[:1])

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__
        )
        logger.info('cluster is %s' % str(cluster_id))
        self.fuel_web.update_nodes(
            cluster_id,
            {'slave-01': ['controller']}
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)
        self.fuel_web.assert_cluster_ready(
            'slave-01', smiles_count=4, networks_count=1, timeout=300)
        self.fuel_web.run_single_ostf_test(
            cluster_id=cluster_id, test_sets=['sanity'],
            test_name=('fuel_health.tests.sanity.test_sanity_identity'
                       '.SanityIdentityTest.test_list_users'))


@test(groups=["thread_2"])
class SimpleFlat(TestBasic):
    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["smoke", "deploy_simple_flat"])
    @log_snapshot_on_error
    def deploy_simple_flat(self):
        """Deploy cluster in simple mode with flat nova-network

        Scenario:
            1. Create cluster
            2. Add 1 node with controller role
            3. Add 1 node with compute role
            4. Deploy the cluster
            5. Validate cluster was set up correctly, there are no dead
            services, there are no errors in logs
            6. Verify networks
            7. Verify network configuration on controller
            8. Run OSTF

        Snapshot: deploy_simple_flat

        """
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

        task = self.fuel_web.run_network_verify(cluster_id)
        self.fuel_web.assert_task_success(task, 60 * 2, interval=10)

        self.env.verify_network_configuration("slave-01")

        self.fuel_web.run_ostf(
            cluster_id=cluster_id,
            should_fail=2,
            failed_test_name=['Create volume and attach it to instance',
                              #TODO: issue with remove floating ip
                              # https://bugs.launchpad.net/fuel/+bug/1263916
                              ])

        self.env.make_snapshot("deploy_simple_flat")

    @test(depends_on=[deploy_simple_flat],
          groups=["simple_flat_node_deletion"])
    @log_snapshot_on_error
    def simple_flat_node_deletion(self):
        """Remove controller from cluster in simple mode with flat nova-network

         Scenario:
            1. Revert "simple flat" environment
            2. Remove controller nodes
            3. Deploy changes
            4. Verify node returns to unallocated pull

        """
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
            timeout=10 * 60
        )

    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["simple_flat_blocked_vlan"])
    @log_snapshot_on_error
    def simple_flat_blocked_vlan(self):
        """Verify network verification with blocked VLANs

        Scenario:
            1. Create cluster
            2. Add 1 node with controller role
            3. Add 1 node with compute role
            4. Deploy the cluster
            5. Validate cluster was set up correctly, there are no dead
            services, there are no errors in logs
            6. Block first VLAN
            7. Run Verify network and assert it fails
            8. Restore first VLAN

        """
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

        ebtables = self.env.get_ebtables(
            cluster_id, self.env.nodes().slaves[:2])
        ebtables.restore_vlans()
        try:
            ebtables.block_first_vlan()
            task = self.fuel_web.run_network_verify(cluster_id)
            self.fuel_web.assert_task_failed(task, 60 * 2)
        finally:
            ebtables.restore_first_vlan()

    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["simple_flat_add_compute"])
    @log_snapshot_on_error
    def simple_flat_add_compute(self):
        """Add compute node to cluster in simple mode

        Scenario:
            1. Create cluster
            2. Add 1 node with controller role
            3. Add 1 node with compute role
            4. Deploy the cluster
            5. Validate cluster was set up correctly, there are no dead
            services, there are no errors in logs
            6. Add 1 node with role compute
            7. Deploy changes
            8. Validate cluster was set up correctly, there are no dead
            services, there are no errors in logs
            9. Verify services list on compute nodes
            10. Run OSTF

        Snapshot: simple_flat_add_compute

        """
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

        self.fuel_web.update_nodes(
            cluster_id, {'slave-03': ['compute']}, True, False)
        self.fuel_web.deploy_cluster_wait(cluster_id)

        assert_equal(
            3, len(self.fuel_web.client.list_cluster_nodes(cluster_id)))

        self.fuel_web.assert_cluster_ready(
            "slave-01", smiles_count=8, networks_count=1, timeout=300)
        self.env.verify_node_service_list("slave-02", 8)
        self.env.verify_node_service_list("slave-03", 8)

        self.fuel_web.run_ostf(
            cluster_id=cluster_id,
            should_fail=1,
            failed_test_name=['Create volume and attach it to instance'])

        self.env.make_snapshot("simple_flat_add_compute")


@test(groups=["thread_2"])
class SimpleVlan(TestBasic):
    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["deploy_simple_vlan"])
    @log_snapshot_on_error
    def deploy_simple_vlan(self):
        """Deploy cluster in simple mode with nova-network VLAN Manager

        Scenario:
            1. Create cluster
            2. Add 1 node with controller role
            3. Add 1 node with compute role
            4. Set up cluster to use Network VLAN manager with 8 networks
            5. Deploy the cluster
            6. Validate cluster was set up correctly, there are no dead
            services, there are no errors in logs
            7. Run network verification
            8. Run OSTF

        Snapshot: deploy_simple_vlan

        """
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

        task = self.fuel_web.run_network_verify(cluster_id)
        self.fuel_web.assert_task_success(task, 60 * 2, interval=10)

        self.fuel_web.run_ostf(
            cluster_id=cluster_id,
            should_fail=1,
            failed_test_name=['Create volume and attach it to instance'])

        self.env.make_snapshot("deploy_simple_vlan")


@test(groups=["thread_2", "multirole"])
class MultiroleControllerCinder(TestBasic):
    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["deploy_multirole_controller_cinder"])
    @log_snapshot_on_error
    def deploy_multirole_controller_cinder(self):
        """Deploy cluster in simple mode with multi-role controller and cinder

        Scenario:
            1. Create cluster
            2. Add 1 node with controller and cinder roles
            3. Add 1 node with compute role
            4. Deploy the cluster
            5. Run network verification
            6. Run OSTF

        Snapshot: deploy_multirole_controller_cinder

        """
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

        self.fuel_web.verify_network(cluster_id)

        self.fuel_web.run_ostf(cluster_id=cluster_id)

        self.env.make_snapshot("deploy_multirole_controller_cinder")


@test(groups=["thread_2", "multirole"])
class MultiroleComputeCinder(TestBasic):
    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["deploy_multirole_compute_cinder"])
    @log_snapshot_on_error
    def deploy_multirole_compute_cinder(self):
        """Deploy cluster in simple mode with multi-role compute and cinder

        Scenario:
            1. Create cluster
            2. Add 1 node with controller role
            3. Add 2 node with compute and cinder roles
            4. Deploy the cluster
            5. Run network verification
            6. Run OSTF

        Snapshot: deploy_multirole_compute_cinder

        """
        self.env.revert_snapshot("ready_with_3_slaves")

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE_SIMPLE
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['compute', 'cinder'],
                'slave-03': ['compute', 'cinder']
            }
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)

        self.fuel_web.verify_network(cluster_id)

        self.fuel_web.run_ostf(cluster_id=cluster_id)

        self.env.make_snapshot("deploy_multirole_compute_cinder")


@test(groups=["thread_2"])
class UntaggedNetwork(TestBasic):
    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["deploy_untagged_network"])
    @log_snapshot_on_error
    def deploy_untagged_network(self):
        """Deploy cluster with untagged networks

        Scenario:
            1. Create cluster
            2. Add 1 node with controller role
            3. Add 1 node with compute role
            4. Split networks on existing physical interfaces
            5. Remove VLAN tagging from networks which are not on eth0
            6. Run network verification
            7. Deploy the cluster
            8. Run network verification

        Snapshot: deploy_untagged_network

        """
        self.env.revert_snapshot("ready_with_3_slaves")

        vlan_turn_off = {'vlan_start': None}
        interfaces = {
            'eth1': ["public", "floating"],
            'eth2': ["management"],
            'eth3': ["fixed"],
            'eth4': ["storage"]
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
        [net.update(vlan_turn_off)
         for net in nets if net["name"] != "storage"]

        # stop using VLANs:
        self.fuel_web.client.update_network(cluster_id, networks=nets)

        self.fuel_web.verify_network(cluster_id)

        self.fuel_web.deploy_cluster_wait(cluster_id)
        self.fuel_web.assert_cluster_ready(
            'slave-01', smiles_count=6, networks_count=1, timeout=300)

        self.fuel_web.verify_network(cluster_id)

        self.env.make_snapshot("deploy_untagged_network")


@test(groups=["thread_2"])
class FloatingIPs(TestBasic):
    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["deploy_floating_ips"])
    @log_snapshot_on_error
    def deploy_floating_ips(self):
        """Deploy cluster with non-default 3 floating IPs ranges

        Scenario:
            1. Create cluster
            2. Add 1 node with controller role
            3. Add 1 node with compute and cinder roles
            4. Update floating IP ranges. Use 3 ranges
            5. Deploy the cluster
            6. Verify available floating IP list
            7. Run OSTF

        Snapshot: deploy_floating_ips

        """
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
                networks['networks'][interface]['ip_ranges'] = \
                    self.fuel_web.get_floating_ranges()[0]
                break

        self.fuel_web.client.update_network(
            cluster_id,
            net_manager=networks['net_manager'],
            networks=networks['networks']
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)

        # assert ips
        expected_ips = self.fuel_web.get_floating_ranges()[1]
        self.fuel_web.assert_cluster_floating_list('slave-02', expected_ips)

        self.fuel_web.run_ostf(
            cluster_id=cluster_id,
            should_fail=1,
            failed_test_name=['Create volume and attach it to instance'])

        self.env.make_snapshot("deploy_floating_ips")


class SimpleCinder(TestBasic):
    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["deploy_simple_cinder"])
    @log_snapshot_on_error
    def deploy_simple_cinder(self):
        """Deploy cluster in simple mode with cinder

        Scenario:
            1. Create cluster
            2. Add 1 node with controller role
            3. Add 1 node with compute role
            4. Add 1 node with cinder role
            5. Deploy the cluster
            6. Validate cluster was set up correctly, there are no dead
            services, there are no errors in logs
            7. Run OSTF

        Snapshot: deploy_simple_cinder

        """
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

        self.fuel_web.run_ostf(cluster_id=cluster_id)

        self.env.make_snapshot("deploy_simple_cinder")


@test(groups=["thread_1"])
class NodeMultipleInterfaces(TestBasic):
    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["deploy_node_multiple_interfaces"])
    @log_snapshot_on_error
    def deploy_node_multiple_interfaces(self):
        """Deploy cluster with networks allocated on different interfaces

        Scenario:
            1. Create cluster
            2. Add 1 node with controller role
            3. Add 1 node with compute role
            4. Add 1 node with cinder role
            5. Split networks on existing physical interfaces
            6. Deploy the cluster
            7. Verify network configuration on each deployed node
            8. Run network verification

        Snapshot: deploy_node_multiple_interfaces

        """
        self.env.revert_snapshot("ready_with_3_slaves")

        interfaces_dict = {
            'eth1': ['floating', 'public'],
            'eth2': ['storage'],
            'eth3': ['fixed'],
            'eth4': ['management'],
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

        task = self.fuel_web.run_network_verify(cluster_id)
        self.fuel_web.assert_task_success(task, 60 * 2, interval=10)

        self.env.make_snapshot("deploy_node_multiple_interfaces")


@test(groups=["thread_1"])
class NodeDiskSizes(TestBasic):
    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["check_nodes_notifications"])
    @log_snapshot_on_error
    def check_nodes_notifications(self):
        """Verify nailgun notifications for discovered nodes

        Scenario:
            1. Revert snapshot "ready_with_3_slaves"
            2. Verify hard drive sizes for discovered nodes in /api/nodes
            3. Verify hard drive sizes for discovered nodes in notifications

        """
        self.env.revert_snapshot("ready_with_3_slaves")

        # assert /api/nodes
        disk_size = NODE_VOLUME_SIZE * 1024 ** 3
        nailgun_nodes = self.fuel_web.client.list_nodes()
        for node in nailgun_nodes:
            for disk in node['meta']['disks']:
                assert_equal(disk['size'], disk_size, 'Disk size')

        hdd_size = "{} TB HDD".format(float(disk_size * 3 / (10 ** 9)) / 1000)
        notifications = self.fuel_web.client.get_notifications()
        for node in nailgun_nodes:
            # assert /api/notifications
            for notification in notifications:
                discover = notification['topic'] == 'discover'
                current_node = notification['node_id'] == node['id']
                if current_node and discover:
                    assert_true(hdd_size in notification['message'])

            # assert disks
            disks = self.fuel_web.client.get_node_disks(node['id'])
            for disk in disks:
                assert_equal(disk['size'],
                             NODE_VOLUME_SIZE * 1024 - 500, 'Disk size')

    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["check_nodes_disks"])
    @log_snapshot_on_error
    def check_nodes_disks(self):
        """Verify nailgun notifications for discovered nodes

        Scenario:
            1. Create cluster
            2. Add 1 node with controller role
            3. Add 1 node with compute role
            4. Add 1 node with cinder role
            5. Deploy the cluster
            6. Verify hard drive sizes for deployed nodes

        """

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

        self.fuel_web.run_ostf(cluster_id=cluster_id)

        nodes_dict = {
            'slave-01': ['controller'],
            'slave-02': ['compute'],
            'slave-03': ['cinder']
        }

        # assert node disks after deployment
        for node_name in nodes_dict:
            str_block_devices = self.fuel_web.get_cluster_block_devices(
                node_name)

            logger.debug("Block device:\n{}".format(str_block_devices))

            expected_regexp = re.compile(
                "vda\s+\d+:\d+\s+0\s+{}G\s+0\s+disk".format(NODE_VOLUME_SIZE))
            assert_true(
                expected_regexp.search(str_block_devices),
                "Unable to find vda block device for {}G in: {}".format(
                    NODE_VOLUME_SIZE, str_block_devices
                ))

            expected_regexp = re.compile(
                "vdb\s+\d+:\d+\s+0\s+{}G\s+0\s+disk".format(NODE_VOLUME_SIZE))
            assert_true(
                expected_regexp.search(str_block_devices),
                "Unable to find vdb block device for {}G in: {}".format(
                    NODE_VOLUME_SIZE, str_block_devices
                ))

            expected_regexp = re.compile(
                "vdc\s+\d+:\d+\s+0\s+{}G\s+0\s+disk".format(NODE_VOLUME_SIZE))
            assert_true(
                expected_regexp.search(str_block_devices),
                "Unable to find vdc block device for {}G in: {}".format(
                    NODE_VOLUME_SIZE, str_block_devices
                ))


@test(groups=["thread_2"])
class MultinicBootstrap(TestBasic):
    @test(depends_on=[SetupEnvironment.prepare_release],
          groups=["multinic_bootstrap_booting"])
    @log_snapshot_on_error
    def multinic_bootstrap_booting(self):
        """Verify slaves booting with blocked mac address

        Scenario:
            1. Revert snapshot "ready"
            2. Block traffic for first slave node (by mac)
            3. Restore mac addresses and boot first slave
            4. Verify slave mac addresses is equal to unblocked

        """
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
    @test(depends_on=[SimpleFlat.deploy_simple_flat],
          groups=["delete_environment"])
    @log_snapshot_on_error
    def delete_environment(self):
        """Delete existing environment
        and verify nodes returns to unallocated state

        Scenario:
            1. Revert "simple flat" environment
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
            timeout=10 * 60,
            interval=15
        )


@test(groups=["thread_1"])
class UntaggedNetworksNegative(TestBasic):
    @test(
        depends_on=[SetupEnvironment.prepare_slaves_3],
        groups=["untagged_networks_negative"],
        enabled=False)
    @log_snapshot_on_error
    def untagged_networks_negative(self):
        """Verify network verification fails with untagged network on eth0

        Scenario:
            1. Create cluster
            2. Add 1 node with controller role
            3. Add 1 node with compute role
            4. Split networks on existing physical interfaces
            5. Remove VLAN tagging from networks which are on eth0
            6. Run network verification (assert it fails)
            7. Start cluster deployment (assert it fails)

        """
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
