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

from proboscis.asserts import assert_true
from proboscis import test
from devops.helpers.helpers import wait
from fuelweb_test import settings
from fuelweb_test.helpers import os_actions
from fuelweb_test.helpers.decorators import log_snapshot_on_error
from fuelweb_test.tests.base_test_case import SetupEnvironment
from fuelweb_test.tests.base_test_case import TestBasic
from fuelweb_test import logger


@test(groups=["vcenter"])
class VcenterDeploy(TestBasic):
    @test(depends_on=[SetupEnvironment.prepare_slaves_1],
          groups=["smoke", "vcenter_one_node_simple"])
    @log_snapshot_on_error
    def vcenter_one_node_simple(self):
        """Deploy cluster with controller node only

        Scenario:
            1. Create cluster
            2. Add 1 node with controller role
            3. Deploy the cluster
            4. Validate cluster was set up correctly, there are no dead
            5. Create instance and delete instance.

        """
        self.env.revert_snapshot("ready_with_1_slaves")

        # Configure cluster
        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=settings.DEPLOYMENT_MODE_SIMPLE,
            settings={
                'use_vcenter': True,
                'host_ip': settings.VCENTER_IP,
                'vc_user': settings.VCENTER_USERNAME,
                'vc_password': settings.VCENTER_PASSWORD,
                'cluster': settings.VCENTER_CLUSTERS
            }
        )
        logger.info("cluster is {}".format(cluster_id))

        # Add nodes to roles
        self.fuel_web.update_nodes(
            cluster_id,
            {'slave-01': ['controller']}
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)

        # Wait until nova-compute get information about clusters
        # Fix me. Later need to change sleep with wait function.
        time.sleep(60)

        self.fuel_web.run_ostf(
            cluster_id=cluster_id, should_fail=1)

    @test(depends_on=[SetupEnvironment.prepare_slaves_1],
          groups=["vcenter_multiple_cluster"])
    @log_snapshot_on_error
    def vcenter_multiple_cluster(self):
        """Deploy cluster with controller node only and test Vcenter
           multiple clusters support feature

        Scenario:
            1. Create cluster
            2. Add 1 node with controller role
            3. Deploy the cluster
            4. Check that available at least two hypervisor
            5. Create 4 instances
            6. Check connectivity between 2 instances in different hypervisor
        """
        self.env.revert_snapshot("ready_with_1_slaves")

        # Configure cluster
        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=settings.DEPLOYMENT_MODE_SIMPLE,
            settings={
                'use_vcenter': True,
                'host_ip': settings.VCENTER_IP,
                'vc_user': settings.VCENTER_USERNAME,
                'vc_password': settings.VCENTER_PASSWORD,
                'cluster': settings.VCENTER_CLUSTERS
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
        logger.info("Controller ip is {}".format(ctrl_ip))
        os = os_actions.OpenStackActions(ctrl_ip)
        hypervisors = os.get_hypervisors()

        # Check hypervisor quantity and create instances
        assert_true(len(hypervisors) > 1, 'Not enoght vCenter clusters.')
        if len(hypervisors) > 1:
            logger.info("Create Instances and assign floating ips:")
            for i in range(1, 5):
                srv = os.create_server_for_migration()
                logger.info(os.get_instance_detail(srv).to_dict()['name'])
                os.assign_floating_ip(srv)

        # Check that there are instanses on each hypervisor
        # Fix me. Later need to change sleep with wait function.
        time.sleep(30)
        hypervisors = os.get_hypervisors()
        for hypervisor in hypervisors:
            assert_true(os.get_hypervisor_vms_count(hypervisor) != 0,
                        "No active VMs on " +
                        os.get_hypervisor_hostanme(hypervisor))
            logger.info("{} active VMs  on Hypervisor {}".format(
                        os.get_hypervisor_vms_count(hypervisor),
                        os.get_hypervisor_hostanme(hypervisor)))

        # Get instances ips from different hypervisors
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
        res = os.execute_through_host(ssh, ips_for_check[0],
                                      "ping -q -c3 " + ips_for_check[1] +
                                      " | grep received | grep -v '0% packet \
                                      loss'")
        assert_true(res == "", "Error in Instances network connectivity.\n" +
                    str(res))

    @test(depends_on=[SetupEnvironment.prepare_slaves_1],
          groups=["vcenter_vmdk"])
    @log_snapshot_on_error
    def vcenter_vmdk(self):
        """Deploy cluster with controller node only and test VMDK
           driver support feature

        Scenario:
            1. Create cluster
            2. Add 1 node with controller and cinder roles
            3. Deploy the cluster
            4. Run osft
        """
        self.env.revert_snapshot("ready_with_1_slaves")

        # Configure cluster
        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=settings.DEPLOYMENT_MODE_SIMPLE,
            settings={
                'use_vcenter': True,
                'host_ip': settings.VCENTER_IP,
                'vc_user': settings.VCENTER_USERNAME,
                'vc_password': settings.VCENTER_PASSWORD,
                'cluster': settings.VCENTER_CLUSTERS
            }
        )
        logger.info("cluster is {0}".format(cluster_id))

        # Add nodes to roles
        self.fuel_web.update_nodes(
            cluster_id,
            {'slave-01': ['controller', 'cinder']}
        )
        # Deploy cluster
        self.fuel_web.deploy_cluster_wait(cluster_id)

        # Wait until nova-compute get information about clusters
        # Fix me. Later need to change sleep with wait function.
        time.sleep(60)

        self.fuel_web.run_single_ostf_test(
            cluster_id=cluster_id, test_sets=['smoke'],
            test_name=('fuel_health.tests.smoke.'
                       'test_create_volume.'
                       'VolumesTest.'
                       'test_volume_create')
        )

    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["vcenter_ha"])
    @log_snapshot_on_error
    def vcenter_ha(self):
        """Deploy cluster with 3 controller nodes and run osft

        Scenario:
            1. Create cluster
            2. Add 3 nodes with controller role
            3. Deploy the cluster
            4. Run osft
        """
        self.env.revert_snapshot("ready_with_3_slaves")

        # Configure cluster
        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE_HA,
            settings={
                'use_vcenter': True,
                'host_ip': settings.VCENTER_IP,
                'vc_user': settings.VCENTER_USERNAME,
                'vc_password': settings.VCENTER_PASSWORD,
                'cluster': settings.VCENTER_CLUSTERS
            }
        )
        logger.info("cluster is {0}".format(cluster_id))

        # Add nodes to roles
        self.fuel_web.update_nodes(
            cluster_id,
            {'slave-01': ['controller'],
             'slave-02': ['controller'],
             'slave-03': ['controller']}
        )
        # Deploy cluster
        self.fuel_web.deploy_cluster_wait(cluster_id)

        # Wait until nova-compute get information about clusters
        # Fix me. Later need to change sleep with wait function.
        time.sleep(60)

        self.fuel_web.run_ostf(
            cluster_id=cluster_id, should_fail=1)
