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

from devops.helpers.helpers import wait
from proboscis.asserts import assert_true
from proboscis import test

from fuelweb_test.helpers.decorators import log_snapshot_on_error
from fuelweb_test.helpers import os_actions
from fuelweb_test import logger
from fuelweb_test.settings import DEPLOYMENT_MODE_SIMPLE
from fuelweb_test.settings import DEPLOYMENT_MODE_HA
from fuelweb_test.settings import VCENTER_IP
from fuelweb_test.settings import VCENTER_USERNAME
from fuelweb_test.settings import VCENTER_PASSWORD
from fuelweb_test.settings import VCENTER_CLUSTERS
from fuelweb_test.tests.base_test_case import SetupEnvironment
from fuelweb_test.tests.base_test_case import TestBasic


@test(groups=["vcenter"])
class VcenterDeploy(TestBasic):
    @test(depends_on=[SetupEnvironment.prepare_slaves_1],
          groups=["smoke", "vcenter_one_node_simple"])
    @log_snapshot_on_error
    def vcenter_one_node_simple(self):
        """Deploy vcenter cluster with controller node only

        Scenario:
            1. Create cluster
            2. Add 1 node with controller role
            3. Deploy the cluster
            4. Verify that the cluster was set up correctly, there are no
               dead services
            5. Create instance and delete instance

        """
        self.env.revert_snapshot("ready_with_1_slaves")

        # Configure cluster
        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE_SIMPLE,
            settings={
                'host_ip': VCENTER_IP,
                'vc_user': VCENTER_USERNAME,
                'vc_password': VCENTER_PASSWORD,
                'cluster': VCENTER_CLUSTERS
            }
        )
        logger.info("cluster is {}".format(cluster_id))

        # Assign role to node
        self.fuel_web.update_nodes(
            cluster_id,
            {'slave-01': ['controller']}
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)

        # Wait until nova-compute get information about clusters
        # Fix me. Later need to change sleep with wait function.
        time.sleep(60)

        self.fuel_web.run_ostf(
            cluster_id=cluster_id, test_sets=['smoke', 'sanity'])

    @test(depends_on=[SetupEnvironment.prepare_slaves_1],
          groups=["vcenter_multiple_cluster"])
    @log_snapshot_on_error
    def vcenter_multiple_cluster(self):
        """Deploy cluster with one controller and test vCenter
           multiple vSphere clusters support

        Scenario:
            1. Create cluster
            2. Add 1 node with controller role
            3. Deploy the cluster
            4. Check that available at least two hypervisors (vSphere clusters)
            5. Create 4 instances
            6. Check connectivity between 2 instances that are running in
               different vSphere clusters

        """
        self.env.revert_snapshot("ready_with_1_slaves")

        # Configure cluster
        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE_SIMPLE,
            settings={
                'host_ip': VCENTER_IP,
                'vc_user': VCENTER_USERNAME,
                'vc_password': VCENTER_PASSWORD,
                'cluster': VCENTER_CLUSTERS
            }
        )
        logger.info("cluster is {0}".format(cluster_id))

        # Add nodes to roles
        self.fuel_web.update_nodes(
            cluster_id,
            {'slave-01': ['controller']}
        )
        # Deploy cluster
        self.fuel_web.deploy_cluster_wait(cluster_id)

        # Wait until nova-compute get information about clusters
        # Fix me. Later need to change sleep with wait function.
        time.sleep(60)

        ctrl_ip = self.fuel_web.get_nailgun_node_by_name('slave-01')['ip']
        logger.info("Controller IP is {}".format(ctrl_ip))
        os = os_actions.OpenStackActions(ctrl_ip)
        hypervisors = os.get_hypervisors()

        # Check hypervisor quantity and create instances
        assert_true(len(hypervisors) > 1, 'Not enough vCenter clusters.')
        if len(hypervisors) > 1:
            logger.info("Create instances and assign floating IPs:")
            for i in range(1, 6):
                srv = os.create_server_for_migration(timeout=300)
                logger.info(os.get_instance_detail(srv).to_dict()['name'])
                os.assign_floating_ip(srv)

        # Check that there are instanses on each hypervisor
        # Fix me. Later need to change sleep with wait function.
        time.sleep(30)
        hypervisors = os.get_hypervisors()
        for hypervisor in hypervisors:
            assert_true(os.get_hypervisor_vms_count(hypervisor) != 0,
                        "No active VMs on " +
                        os.get_hypervisor_hostname(hypervisor))
            logger.info("{} active VMs on Hypervisor {}".format(
                        os.get_hypervisor_vms_count(hypervisor),
                        os.get_hypervisor_hostname(hypervisor)))

        # Get instances IPs from different hypervisors
        servers_for_check = {}
        ips_for_check = []
        servers = os.get_servers()
        for server in servers:
            if os.get_srv_hypervisor_name(server) not in servers_for_check:
                servers_for_check[os.get_srv_hypervisor_name(server)] = {}
                server_detail = os.get_instance_detail(server).to_dict()
                for net_prefs in server_detail['addresses']['novanetwork']:
                    if net_prefs['OS-EXT-IPS:type'] == 'floating' and \
                       net_prefs['addr'] not in ips_for_check and \
                       len(ips_for_check) == 0:
                        ips_for_check.append(net_prefs['addr'])
                    if net_prefs['OS-EXT-IPS:type'] == 'fixed' and \
                       len(ips_for_check) == 1:
                        ips_for_check.append(net_prefs['addr'])

        # Wait until vm is booted
        ssh = self.env.get_ssh_to_remote_by_name("slave-01")
        wait(
            lambda: not ssh.execute('curl -s -m1 http://' + ips_for_check[0] +
                                    ':22 |grep -iq "[a-z]"')['exit_code'],
            interval=10, timeout=100)
        # Check server's connectivity
        res = int(os.execute_through_host(ssh, ips_for_check[0],
                                          "ping -q -c3 " + ips_for_check[1] +
                                          " 2>/dev/null >/dev/null;"
                                          " echo -n $?"))
        assert_true(res == 0, "Error in Instances network connectivity.")

    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["vcenter_vmdk"])
    @log_snapshot_on_error
    def vcenter_vmdk(self):
        """Deploy cluster with controller and cinder nodes and run checks

        Scenario:
            1. Create cluster
            2. Add 2 nodes
               1 controller
               1 cinder (VMDK backend)
            3. Deploy the cluster
            4. Run OSTF
        """
        self.env.revert_snapshot("ready_with_3_slaves")

        # Configure cluster
        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE_SIMPLE,
            settings={
                'volumes_vmdk': True,
                'volumes_lvm': False,
                'host_ip': VCENTER_IP,
                'vc_user': VCENTER_USERNAME,
                'vc_password': VCENTER_PASSWORD,
                'cluster': VCENTER_CLUSTERS,
                'tenant': 'vcenter',
                'user': 'vcenter',
                'password': 'vcenter'
            }
        )
        logger.info("cluster is {0}".format(cluster_id))

        # Assign roles to nodes
        self.fuel_web.update_nodes(
            cluster_id,
            {'slave-01': ['controller'],
             'slave-02': ['cinder']}
        )
        # Deploy cluster
        self.fuel_web.deploy_cluster_wait(cluster_id)

        # Wait until nova-compute get information about clusters
        # FIXME: Later need to change sleep with wait function.
        time.sleep(60)

        self.fuel_web.run_ostf(
            cluster_id=cluster_id, test_sets=['smoke', 'sanity'])

    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["vcenter_ha"])
    @log_snapshot_on_error
    def vcenter_ha(self):
        """Deploy cluster with 3 controllers and run OSTF

        Scenario:
            1. Create cluster
            2. Add 3 nodes with controller role
            3. Deploy the cluster
            4. Run OSTF

        """
        self.env.revert_snapshot("ready_with_3_slaves")

        # Configure cluster
        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE_HA,
            settings={
                'host_ip': VCENTER_IP,
                'vc_user': VCENTER_USERNAME,
                'vc_password': VCENTER_PASSWORD,
                'cluster': VCENTER_CLUSTERS,
                'tenant': 'vcenter',
                'user': 'vcenter',
                'password': 'vcenter'
            }
        )
        logger.info("cluster is {0}".format(cluster_id))

        # Add nodes to roles
        self.fuel_web.update_nodes(
            cluster_id,
            {'slave-01': ['controller'],
             'slave-02': ['controller'],
             'slave-03': ['controller']
             }
        )
        # Deploy cluster
        self.fuel_web.deploy_cluster_wait(cluster_id)

        # Wait until nova-compute get information about clusters
        # Fix me. Later need to change sleep with wait function.
        time.sleep(60)

        self.fuel_web.run_ostf(
            cluster_id=cluster_id, test_sets=['ha', 'smoke', 'sanity'])

    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["vcenter_simple_add_cinder"])
    @log_snapshot_on_error
    def vcenter_simple_add_cinder(self):
        """Deploy cluster with one controller and cinder node

        Scenario:
            1. Create cluster
            2. Add 1 node with role controller
            3. Deploy the cluster
            4. Check network connectivity and run OSTF
            5. Add 1 cinder node to the cluster
            6. Re-deploy the cluster
            7. Check network connectivity and run OSTF

        """
        self.env.revert_snapshot("ready_with_3_slaves")

        # Configure cluster
        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE_SIMPLE,
            settings={
                'volumes_lvm': False,
                'volumes_vmdk': True,
                'host_ip': VCENTER_IP,
                'vc_user': VCENTER_USERNAME,
                'vc_password': VCENTER_PASSWORD,
                'cluster': VCENTER_CLUSTERS,
                'tenant': 'vcenter',
                'user': 'vcenter',
                'password': 'vcenter'
            }
        )
        logger.info("cluster is {0}".format(cluster_id))

        # Add nodes to roles
        self.fuel_web.update_nodes(
            cluster_id,
            {'slave-01': ['controller']}
        )
        # Deploy cluster
        self.fuel_web.deploy_cluster_wait(cluster_id)
        self.fuel_web.update_nodes(
            cluster_id,
            {'slave-02': ['cinder']}
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)
        self.fuel_web.verify_network(cluster_id)

        self.fuel_web.run_ostf(
            cluster_id=cluster_id, test_sets=['smoke', 'sanity'])

    @test(depends_on=[SetupEnvironment.prepare_slaves_5],
          groups=["vcenter_ha_deployment_with_cinder"])
    @log_snapshot_on_error
    def vcenter_ha_deployment_with_cinder(self):
        """Deploy HA cluster with standalone cinder node

        Scenario:
            1. Create cluster
            2. Add 4 nodes with roles:
               3 controller
               1 cinder
            3. Deploy cluster
            4. Check network connectivity and run OSTF

        """
        self.env.revert_snapshot("ready_with_5_slaves")

        # Configure cluster
        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE_HA,
            settings={
                'volumes_lvm': False,
                'volumes_vmdk': True,
                'host_ip': VCENTER_IP,
                'vc_user': VCENTER_USERNAME,
                'vc_password': VCENTER_PASSWORD,
                'cluster': VCENTER_CLUSTERS,
                'tenant': 'vcenter',
                'user': 'vcenter',
                'password': 'vcenter'
            }
        )
        logger.info("cluster is {0}".format(cluster_id))

        # Add nodes to roles
        self.fuel_web.update_nodes(
            cluster_id,
            {'slave-01': ['controller'],
             'slave-02': ['controller'],
             'slave-03': ['controller'],
             'slave-04': ['cinder']
             }
        )
        # Deploy cluster
        self.fuel_web.deploy_cluster_wait(cluster_id)
        self.fuel_web.verify_network(cluster_id)

        self.fuel_web.run_ostf(
            cluster_id=cluster_id, test_sets=['ha', 'smoke', 'sanity'])

    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["vcenter_simple_stop_deployment"])
    @log_snapshot_on_error
    def vcenter_simple_stop_deployment(self):
        """Deploy cluster, stop running deployment process, start deployment
           again

        Scenario:
            1. Create cluster
            2. Add 2 nodes with roles:
               1 controller/cinder
               1 cinder
            3. Stop cluster deployment
            4. Wait until nodes will be 'online' again
            5. Re-deploy cluster
            4. Check network connectivity and run OSTF

        """
        self.env.revert_snapshot("ready_with_3_slaves")

        # Configure cluster
        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE_SIMPLE,
            settings={
                'volumes_lvm': False,
                'volumes_vmdk': True,
                'host_ip': VCENTER_IP,
                'vc_user': VCENTER_USERNAME,
                'vc_password': VCENTER_PASSWORD,
                'cluster': VCENTER_CLUSTERS,
                'tenant': 'vcenter',
                'user': 'vcenter',
                'password': 'vcenter'
            }
        )
        logger.info("cluster is {0}".format(cluster_id))

        # Add nodes to roles
        self.fuel_web.update_nodes(
            cluster_id,
            {'slave-01': ['controller', 'cinder'],
             'slave-02': ['cinder']
             }
        )
        self.fuel_web.provisioning_cluster_wait(cluster_id)
        self.fuel_web.deploy_task_wait(cluster_id=cluster_id, progress=40)
        self.fuel_web.stop_deployment_wait(cluster_id)
        self.fuel_web.wait_nodes_get_online_state(
            self.env.get_virtual_environment().nodes().slaves[:2])
        self.fuel_web.deploy_cluster_wait(cluster_id)

        self.fuel_web.run_ostf(
            cluster_id=cluster_id, test_sets=['ha', 'smoke', 'sanity'])

    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["vcenter_vlan_simple", "vcenter_vlan"])
    @log_snapshot_on_error
    def vcenter_vlan_simple(self):
        """Deploy a cluster in Simple mode with 1 controller node,
            1 cinder node, vCenter and VlanManager enabled.
            Verify that it works.

        Scenario:
            1. Create a Simple cluster with vCenter as a hypervisor
            2. Add 1 node with controller and 1 node with cinder roles
            3. Set Nova-Network VlanManager as a network backend
            4. Deploy the cluster
            5. Run network verification
            6. Run OSTF
        """
        self.env.revert_snapshot("ready_with_3_slaves")

        # Configure a cluster.
        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE_SIMPLE,
            settings={
                'volumes_vmdk': True,
                'volumes_lvm': False,
                'host_ip': VCENTER_IP,
                'vc_user': VCENTER_USERNAME,
                'vc_password': VCENTER_PASSWORD,
                'cluster': VCENTER_CLUSTERS,
                'tenant': 'vcenter',
                'user': 'vcenter',
                'password': 'vcenter'
            }
        )
        logger.info("cluster is {0}".format(cluster_id))

        # Assign roles to nodes.
        self.fuel_web.update_nodes(
            cluster_id,
            {'slave-01': ['controller'],
             'slave-02': ['cinder'],
             }
        )

        # Configure network interfaces.
        # Public and Fixed networks are on the same interface
        # because Nova will use the same vSwitch for PortGroups creating
        # as a ESXi' management interface is located in.
        interfaces = {
            'eth0': ["fuelweb_admin"],
            'eth1': ["public", "fixed"],
            'eth2': ["management", ],
            'eth3': [],
            'eth4': ["storage"],
        }

        slave_nodes = self.fuel_web.client.list_cluster_nodes(cluster_id)
        for node in slave_nodes:
            self.fuel_web.update_node_networks(node['id'], interfaces)

        # Configure Nova-Network VLanManager.
        self.fuel_web.update_vlan_network_fixed(
            cluster_id, amount=8, network_size=32)

        # Deploy the cluster.
        self.fuel_web.deploy_cluster_wait(cluster_id)

        # Run tests.
        self.fuel_web.verify_network(cluster_id)

        self.fuel_web.run_ostf(
            cluster_id=cluster_id, test_sets=['smoke', 'sanity'])

    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["vcenter_vlan_ha", "vcenter_vlan"])
    @log_snapshot_on_error
    def vcenter_vlan_ha(self):
        """Deploy a cluster in HA mode with 2 controller node,
            1 controller + cinder node, vCenter and VlanManager enabled.
            Verify that it works.

        Scenario:
            1. Create a Simple cluster with vCenter as a hypervisor
            2. Add 3 nodes with roles:
                 2 controller
                 1 controller+cinder
            3. Set Nova-Network VlanManager as a network backend
            4. Deploy the cluster
            5. Run network verification
            6. Run OSTF
        """
        self.env.revert_snapshot("ready_with_3_slaves")

        # Configure a cluster.
        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE_HA,
            settings={
                'volumes_vmdk': True,
                'volumes_lvm': False,
                'host_ip': VCENTER_IP,
                'vc_user': VCENTER_USERNAME,
                'vc_password': VCENTER_PASSWORD,
                'cluster': VCENTER_CLUSTERS,
                'tenant': 'vcenter',
                'user': 'vcenter',
                'password': 'vcenter'
            }
        )
        logger.info("cluster is {0}".format(cluster_id))

        # Assign roles to nodes.
        self.fuel_web.update_nodes(
            cluster_id,
            {'slave-01': ['controller'],
             'slave-02': ['controller'],
             'slave-03': ['controller', 'cinder'],
             }
        )

        # Configure network interfaces.
        # Public and Fixed networks are on the same interface
        # because Nova will use the same vSwitch for PortGroups creating
        # as a ESXi' management interface is located in.
        interfaces = {
            'eth0': ["fuelweb_admin"],
            'eth1': ["public", "fixed"],
            'eth2': ["management", ],
            'eth3': [],
            'eth4': ["storage"],
        }

        slave_nodes = self.fuel_web.client.list_cluster_nodes(cluster_id)
        for node in slave_nodes:
            self.fuel_web.update_node_networks(node['id'], interfaces)

        # Configure Nova-Network VLanManager.
        self.fuel_web.update_vlan_network_fixed(
            cluster_id, amount=8, network_size=32)

        # Deploy the cluster.
        self.fuel_web.deploy_cluster_wait(cluster_id)

        # Run tests.
        self.fuel_web.verify_network(cluster_id)

        self.fuel_web.run_ostf(
            cluster_id=cluster_id, test_sets=['ha', 'smoke', 'sanity'])
