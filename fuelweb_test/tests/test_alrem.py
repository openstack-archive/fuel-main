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


@test(groups=["alrem"])
class alremVcenterDeploy(TestBasic):
    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["vcenter_vmdk_1_6", "vcenter_multiple_cluster6"])
    @log_snapshot_on_error
    def vcenter_vmdk_1(self):
        """Deploy cluster with controller node only and test VMDK
           driver support feature

        Scenario:
            1. Create cluster
            2. Add 2 nodes with controller and cinder roles
            3. Deploy the cluster
            4. Run osft
        """
        self.env.revert_snapshot("ready_with_3_slaves")

        # Configure cluster
        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=settings.DEPLOYMENT_MODE_SIMPLE,
            settings={
                'use_vcenter': True,
                'volumes_vmdk': True,
                'volumes_lvm': False,
                'host_ip': settings.VCENTER_IP,
                'vc_user': settings.VCENTER_USERNAME,
                'vc_password': settings.VCENTER_PASSWORD,
                'cluster': settings.VCENTER_CLUSTERS,
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
             'slave-02': ['cinder'],
             'slave-03': ['cinder']}
        )
        # Deploy cluster
        self.fuel_web.deploy_cluster_wait(cluster_id)

        # Wait until nova-compute get information about clusters
        # Fix me. Later need to change sleep with wait function.
        time.sleep(60)

        self.fuel_web.verify_network(cluster_id)

        self.fuel_web.run_ostf(
            cluster_id=cluster_id, test_sets=['smoke', 'sanity'],
            #should_fail=1,
            #failed_test_name=[('Launch instance, create snapshot,'
            #                   ' launch instance from snapshot'),
            #                   ]
            )


    @test(depends_on=[SetupEnvironment.prepare_slaves_1],
          groups=["vcenter_vmdk_2", "vcenter_multiple_cluster6"])
    @log_snapshot_on_error
    def vcenter_vmdk_2(self):
        """Deploy cluster with controller node only and test VMDK
           driver support feature

        Scenario:
            1. Create cluster
            2. Add 2 nodes with controller and cinder roles
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
                'volumes_vmdk': True,
                'volumes_lvm': False,
                'host_ip': settings.VCENTER_IP,
                'vc_user': settings.VCENTER_USERNAME,
                'vc_password': settings.VCENTER_PASSWORD,
                'cluster': settings.VCENTER_CLUSTERS,
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
             }
            )
        # Deploy cluster
        self.fuel_web.deploy_cluster_wait(cluster_id)

        # Wait until nova-compute get information about clusters
        # Fix me. Later need to change sleep with wait function.
        time.sleep(60)

        self.fuel_web.run_ostf(
            cluster_id=cluster_id, test_sets=['smoke', 'sanity'],
            #should_fail=1,
            #failed_test_name=[('Launch instance, create snapshot,'
            #                   ' launch instance from snapshot'),
            #                   ]
            )

    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["vcenter_vmdk_3", "vcenter_multiple_cluster6"])
    @log_snapshot_on_error
    def vcenter_vmdk_3(self):
        """Deploy cluster with controller node only and test VMDK
           driver support feature

        Scenario:
            1. Create cluster
            2. Add 2 nodes with controller and cinder roles
            3. Deploy the cluster
            4. Run osft
        """
        self.env.revert_snapshot("ready_with_3_slaves")

        # Configure cluster
        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=settings.DEPLOYMENT_MODE_SIMPLE,
            settings={
                'use_vcenter': True,
                'volumes_vmdk': True,
                'volumes_lvm': False,
                'host_ip': settings.VCENTER_IP,
                'vc_user': settings.VCENTER_USERNAME,
                'vc_password': settings.VCENTER_PASSWORD,
                'cluster': settings.VCENTER_CLUSTERS,
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
             'slave-02': ['cinder'],
             }
            )
        # Deploy cluster
        self.fuel_web.deploy_cluster_wait(cluster_id)

        # Wait until nova-compute get information about clusters
        # Fix me. Later need to change sleep with wait function.
        time.sleep(60)

        self.fuel_web.run_ostf(
            cluster_id=cluster_id, test_sets=['smoke', 'sanity'],
            #should_fail=1,
            #failed_test_name=[('Launch instance, create snapshot,'
            #                   ' launch instance from snapshot'),
            #                   ]
            )



    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["vcenter_vlan"])
    @log_snapshot_on_error
    def vcenter_vlan(self):
        """Deploy cluster with controller node only and test VMDK
           driver support feature

        Scenario:
            1. Create cluster
            2. Add 2 nodes with controller and cinder roles
            3. Deploy the cluster
            4. Run osft
        """
        self.env.revert_snapshot("ready_with_3_slaves")

        # Configure cluster
        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=settings.DEPLOYMENT_MODE_SIMPLE,
            settings={

                'use_vcenter': True,
                'volumes_vmdk': True,
                'volumes_lvm': False,
                'host_ip': settings.VCENTER_IP,
                'vc_user': settings.VCENTER_USERNAME,
                'vc_password': settings.VCENTER_PASSWORD,
                'cluster': settings.VCENTER_CLUSTERS,
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
             'slave-02': ['cinder'],
             'slave-03': ['cinder'],
             }
        )
        # Deploy cluster

        '''
        {"networks":[{"name":"public","ip_ranges":[["172.16.0.2","172.16.0.127"]],
                      "id":2,
                      "meta":{"name":"public",
                              "notation":"ip_ranges",
                              "render_type":null,
                              "map_priority":1,
                              "assign_vip":true,
                              "use_gateway":true,
                              "vlan_start":null,
                              "render_addr_mask":"public",
                              "cidr":"172.16.0.0/24",
                              "configurable":true,
                              "gateway":"172.16.0.1",
                              "ip_range":["172.16.0.2","172.16.0.127"]},
                      "vlan_start":null,
                      "cidr":"172.16.0.0/24",
                      "group_id":1,
                      "gateway":"172.16.0.1"},
                     {"name":"management",
                      "ip_ranges":[["192.168.0.1","192.168.0.254"]],
                      "id":3,
                      "meta":{"name":"management",
                              "notation":"cidr",
                              "render_type":"cidr",
                              "map_priority":2,
                              "assign_vip":true,
                              "use_gateway":false,
                              "vlan_start":101,
                              "render_addr_mask":"internal",
                              "cidr":"192.168.0.0/24",
                              "configurable":true},
                      "vlan_start":101,
                      "cidr":"192.168.0.0/24",
                      "group_id":1,
                      "gateway":null},
                     {"name":"storage",
                      "ip_ranges":[["192.168.1.1","192.168.1.254"]],
                      "id":4,
                      "meta":{"name":"storage",
                              "notation":"cidr",
                              "render_type":"cidr",
                              "map_priority":2,
                              "assign_vip":false,
                              "use_gateway":false,
                              "vlan_start":102,
                              "render_addr_mask":"storage",
                              "cidr":"192.168.1.0/24",
                              "configurable":true},
                      "vlan_start":102,
                      "cidr":"192.168.1.0/24",
                      "group_id":1,
                      "gateway":null},
                     {"name":"fixed",
                      "ip_ranges":[],
                      "id":5,
                      "meta":{"ext_net_data":["fixed_networks_vlan_start","fixed_networks_amount"],
                              "name":"fixed",
                              "notation":null,
                              "render_type":null,
                              "map_priority":2,
                              "assign_vip":false,
                              "use_gateway":false,
                              "vlan_start":null,
                              "render_addr_mask":null,
                              "configurable":false},
                      "vlan_start":null,
                      "cidr":null,
                      "group_id":1,
                      "gateway":null},
                     {"name":"fuelweb_admin",
                      "ip_ranges":[["10.108.0.3","10.108.0.254"]],
                      "id":1,
                      "meta":{"notation":"ip_ranges",
                              "render_type":null,
                              "assign_vip":false,
                              "configurable":false,
                              "unmovable":true,
                              "use_gateway":true,
                              "render_addr_mask":null,
                              "map_priority":0},
                      "vlan_start":null,
                      "cidr":"10.108.0.0/24",
                      "group_id":null,
                      "gateway":null}],
         "networking_parameters":{"dns_nameservers":["8.8.4.4","8.8.8.8"],
                                  "net_manager":"VlanManager",
                                  "fixed_networks_vlan_start":103,
                                  "fixed_networks_cidr":"10.0.0.0/16",
                                  "floating_ranges":[["172.16.0.128","172.16.0.254"]],
                                  "fixed_network_size":32,"fixed_networks_amount":8}}

        '''


        
        networking_parameters = {"dns_nameservers":["8.8.4.4","8.8.8.8"],
                                  "net_manager":"VlanManager",
                                  "fixed_networks_vlan_start":103,
                                  "fixed_networks_cidr":"10.0.0.0/16",
                                  "floating_ranges":[["172.16.0.128","172.16.0.254"]],
                                  "fixed_network_size":32,
                                  "fixed_networks_amount":8
        }
        
        self.fuel_web.client.update_network(
            cluster_id,
            networking_parameters=networking_parameters
        )


#        self.fuel_web.update_vlan_network_fixed(
#            cluster_id, amount=8, network_size=32)

        self.fuel_web.deploy_cluster_wait(cluster_id)

        # Wait until nova-compute get information about clusters
        # Fix me. Later need to change sleep with wait function.
        time.sleep(60)

        self.fuel_web.run_ostf(
            cluster_id=cluster_id, test_sets=['smoke', 'sanity'],
            #should_fail=1,
            #failed_test_name=[('Launch instance, create snapshot,'
            #                  ' launch instance from snapshot'),
            #                   ]
            )

    @test(depends_on=[SetupEnvironment.prepare_slaves_5],
          groups=["vcenter_ha_vmdk_1_6", "vcenter_ha_vmdk_6", "vcenter_multiple_cluster6"])
    @log_snapshot_on_error
    def vcenter_ha_vmdk_1(self):
        """Deploy cluster with 3 controller nodes and run osft

        Scenario:
            1. Create cluster
            2. Add 3 nodes with controller role
            3. Deploy the cluster
            4. Run osft
        """
        self.env.revert_snapshot("ready_with_5_slaves")

        # Configure cluster
        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=settings.DEPLOYMENT_MODE_HA,
            settings={
                'use_vcenter': True,
                'host_ip': settings.VCENTER_IP,
                'vc_user': settings.VCENTER_USERNAME,
                'vc_password': settings.VCENTER_PASSWORD,
                'cluster': settings.VCENTER_CLUSTERS,
                'tenant': 'vcenter',
                'user': 'vcenter',
                'password': 'vcenter',
                'volumes_vmdk': True,
                'volumes_lvm': False,
            }
        )
        logger.info("cluster is {0}".format(cluster_id))

        # Add nodes to roles
        self.fuel_web.update_nodes(
            cluster_id,
            {'slave-01': ['controller'],
             'slave-02': ['controller'],
             'slave-03': ['controller'],
             'slave-04': ['cinder'],
             'slave-05': ['cinder'],
             }
        )
        # Deploy cluster
        self.fuel_web.deploy_cluster_wait(cluster_id)

        # Wait until nova-compute get information about clusters
        # Fix me. Later need to change sleep with wait function.
        time.sleep(60)

        self.fuel_web.verify_network(cluster_id)

        self.fuel_web.run_ostf(
            cluster_id=cluster_id, test_sets=['ha', 'smoke', 'sanity'],
            #should_fail=1,
            #failed_test_name=[('Launch instance, create snapshot,'
            #                   ' launch instance from snapshot'),
            #                  ]
            )


    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["vcenter_ha_vmdk_2_6", "vcenter_ha_vmdk_6", "vcenter_multiple_cluster6"])
    @log_snapshot_on_error
    def vcenter_ha_vmdk_2(self):
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
            mode=settings.DEPLOYMENT_MODE_HA,
            settings={
                'use_vcenter': True,
                'host_ip': settings.VCENTER_IP,
                'vc_user': settings.VCENTER_USERNAME,
                'vc_password': settings.VCENTER_PASSWORD,
                'cluster': settings.VCENTER_CLUSTERS,
                'tenant': 'vcenter',
                'user': 'vcenter',
                'password': 'vcenter',
                'volumes_vmdk': True,
                'volumes_lvm': False,
            }
        )
        logger.info("cluster is {0}".format(cluster_id))

        # Add nodes to roles
        self.fuel_web.update_nodes(
            cluster_id,
            {'slave-01': ['controller'],
             'slave-02': ['controller'],
             'slave-03': ['controller', 'cinder'],
             }
        )
        # Deploy cluster
        self.fuel_web.deploy_cluster_wait(cluster_id)

        # Wait until nova-compute get information about clusters
        # Fix me. Later need to change sleep with wait function.
        time.sleep(60)

        self.fuel_web.verify_network(cluster_id)

        self.fuel_web.run_ostf(
            cluster_id=cluster_id, test_sets=['ha', 'smoke', 'sanity'],
            #should_fail=1,
            #failed_test_name=[('Launch instance, create snapshot,'
            #                   ' launch instance from snapshot'),
            #                  ]
            )
