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

import traceback

from proboscis import test

from fuelweb_test import logger
from fuelweb_test.helpers.decorators import log_snapshot_on_error
from fuelweb_test import settings
from fuelweb_test.tests.base_test_case import SetupEnvironment
from fuelweb_test.tests.base_test_case import TestBasic


@test(groups=["vcenter_glance"])
class VcenterGlanceDeploy(TestBasic):

    # Section with vCenter's tests
    #  with VMDK (set vCenter+glance)

    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["vcenter_vmdk_simple"])
    @log_snapshot_on_error
    def vcenter_vmdk_simple(self):

        """Deploy cluster with controller node only and test VMDK
           driver support feature

        Scenario:
            1. Create cluster
            2. Add 2 nodes with controller and cinder roles
            3. Deploy the cluster
            4. Run osft
        """
        self.env.revert_snapshot("ready_with_3_slaves")
        ext_node_names = ['esxi1', 'esxi2', 'vcenter', 'trusty']
        self.fuel_web.workstation_revert_snapshot(ext_node_names)

        # Configure cluster
        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=settings.DEPLOYMENT_MODE_SIMPLE,
            settings={
                'use_vcenter': True,
                'volumes_lvm': False,
                'volumes_vmdk': True,
                'images_vcenter': settings.IMAGES_VCENTER,
                'host_ip': settings.VCENTER_IP,
                'vc_user': settings.VCENTER_USERNAME,
                'vc_password': settings.VCENTER_PASSWORD,
                'cluster': settings.VCENTER_CLUSTERS,
                'tenant': 'vcenter',
                'user': 'vcenter',
                'password': 'vcenter',
                'vc_datacenter': settings.VC_DATACENTER,
                'vc_datastore': settings.VC_DATASTORE,
                'vc_image_dir': settings.VC_IMAGE_DIR,
                'vc_host': settings.VC_HOST
            }
        )
        logger.info("cluster is {0}".format(cluster_id))

        # Add nodes to roles
        self.fuel_web.update_nodes(
            cluster_id,
            {'slave-01': ['controller'],
             'slave-02': ['cinder']}
        )
        # Deploy cluster
        self.fuel_web.deploy_cluster_wait(cluster_id)
        self.fuel_web.verify_network(cluster_id)
        self.fuel_web.run_ostf(
            cluster_id=cluster_id, test_sets=['smoke', 'sanity'],
            should_fail=1,
            failed_test_name=[('Launch instance, create snapshot,'
                               ' launch instance from snapshot')])
        self.env.make_snapshot("vcenter_vmdk_simple")

    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["vcenter_vmdk_simple_add_node"])
    @log_snapshot_on_error
    def vcenter_vmdk_simple_add_node(self):
        """
        Scenario:
            1. Create cluster
            2. Add 2 nodes with roles:
               1 controller
               1 cinder
            3. Deploy the cluster
            4. Check network connectivity and run osft
            5. Add 1 node with controller role
            6. Re-deploy cluster.
            7. Check network connectivity and run osft
        """
        self.env.revert_snapshot("ready_with_3_slaves")
        ext_node_names = ['esxi1', 'esxi2', 'vcenter', 'trusty']
        self.fuel_web.workstation_revert_snapshot(ext_node_names)

        # Configure cluster
        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=settings.DEPLOYMENT_MODE_SIMPLE,
            settings={
                'use_vcenter': True,
                'volumes_lvm': False,
                'volumes_vmdk': True,
                'images_vcenter': settings.IMAGES_VCENTER,
                'host_ip': settings.VCENTER_IP,
                'vc_user': settings.VCENTER_USERNAME,
                'vc_password': settings.VCENTER_PASSWORD,
                'cluster': settings.VCENTER_CLUSTERS,
                'tenant': 'vcenter',
                'user': 'vcenter',
                'password': 'vcenter',
                'vc_datacenter': settings.VC_DATACENTER,
                'vc_datastore': settings.VC_DATASTORE,
                'vc_image_dir': settings.VC_IMAGE_DIR,
                'vc_host': settings.VC_HOST
            }
        )
        logger.info("cluster is {0}".format(cluster_id))

        # Add nodes to roles
        self.fuel_web.update_nodes(
            cluster_id,
            {'slave-01': ['controller'],
             'slave-02': ['cinder']}
        )
        # Deploy cluster
        self.fuel_web.deploy_cluster_wait(cluster_id)
        self.fuel_web.verify_network(cluster_id)
        self.fuel_web.run_ostf(
            cluster_id=cluster_id, test_sets=['smoke', 'sanity'])
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-03': ['cinder']
            }
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)
        self.fuel_web.verify_network(cluster_id)
        self.fuel_web.run_ostf(
            cluster_id=cluster_id, test_sets=['smoke', 'sanity'])
        self.env.make_snapshot("vcenter_vmdk_simple_add_node")

    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["vcenter_vmdk_ha_reset_node_during_deployment"])
    @log_snapshot_on_error
    def vcenter_vmdk_ha_reset_node_during_deployment(self):

        """
        Scenario:
            1. Create cluster
            2. Add 3 nodes with roles:
               2 controller
               1 controller + 1 cinder
            3. Reset node and then start deployment of cluster
            4. Check network connectivity and run osft
        """
        self.env.revert_snapshot("ready_with_3_slaves")
        ext_node_names = ['esxi1', 'esxi2', 'vcenter', 'trusty']
        self.fuel_web.workstation_revert_snapshot(ext_node_names)

        # Configure cluster
        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=settings.DEPLOYMENT_MODE_HA,
            settings={
                'use_vcenter': True,
                'volumes_lvm': False,
                'volumes_vmdk': True,
                'images_vcenter': settings.IMAGES_VCENTER,
                'host_ip': settings.VCENTER_IP,
                'vc_user': settings.VCENTER_USERNAME,
                'vc_password': settings.VCENTER_PASSWORD,
                'cluster': settings.VCENTER_CLUSTERS,
                'tenant': 'vcenter',
                'user': 'vcenter',
                'password': 'vcenter',
                'vc_datacenter': settings.VC_DATACENTER,
                'vc_datastore': settings.VC_DATASTORE,
                'vc_image_dir': settings.VC_IMAGE_DIR,
                'vc_host': settings.VC_HOST
            }
        )
        logger.info("cluster is {0}".format(cluster_id))

        # Add nodes to roles
        self.fuel_web.update_nodes(
            cluster_id,
            {'slave-01': ['controller'],
             'slave-02': ['controller'],
             'slave-03': ['controller', 'cinder']
             }
        )
        self.fuel_web.deploy_cluster_wait_progress(cluster_id, progress=30)
        self.fuel_web.warm_restart_nodes(self.env.nodes().slaves[1])
        self.fuel_web.deploy_cluster_wait_progress(cluster_id, progress=100)
        self.fuel_web.verify_network(cluster_id)
        self.fuel_web.run_ostf(
            cluster_id=cluster_id, test_sets=['ha', 'smoke', 'sanity'])
        self.env.make_snapshot("vcenter_vmdk_ha_reset_node_during_deployment")

    @test(depends_on=[SetupEnvironment.prepare_slaves_5],
          groups=["vcenter_vmdk_ha_stop_deployment"])
    @log_snapshot_on_error
    def vcenter_vmdk_ha_stop_deployment(self):
        """
        Scenario:
            1. Create cluster
            2. Add 4 nodes with roles:
               3 controller
               1 cinder
            3. Start deployment of cluster
               then stop deployment
               wait when it will be finished
               and then re-deploy it again
            4. Check network connectivity and run osft
        """
        self.env.revert_snapshot("ready_with_5_slaves")
        ext_node_names = ['esxi1', 'esxi2', 'vcenter', 'trusty']
        self.fuel_web.workstation_revert_snapshot(ext_node_names)

        # Configure cluster
        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=settings.DEPLOYMENT_MODE_HA,
            settings={
                'use_vcenter': True,
                'volumes_lvm': False,
                'volumes_vmdk': True,
                'images_vcenter': settings.IMAGES_VCENTER,
                'host_ip': settings.VCENTER_IP,
                'vc_user': settings.VCENTER_USERNAME,
                'vc_password': settings.VCENTER_PASSWORD,
                'cluster': settings.VCENTER_CLUSTERS,
                'tenant': 'vcenter',
                'user': 'vcenter',
                'password': 'vcenter',
                'vc_datacenter': settings.VC_DATACENTER,
                'vc_datastore': settings.VC_DATASTORE,
                'vc_image_dir': settings.VC_IMAGE_DIR,
                'vc_host': settings.VC_HOST
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
        self.fuel_web.provisioning_cluster_wait(cluster_id)
        self.fuel_web.deploy_task_wait(cluster_id=cluster_id, progress=40)
        try:
                self.fuel_web.stop_deployment_wait(cluster_id)
        except Exception:
                    logger.debug(traceback.format_exc())
        self.fuel_web.wait_nodes_get_online_state(
            self.env.nodes().slaves[:4])
        self.fuel_web.deploy_cluster_wait(cluster_id)
        self.fuel_web.verify_network(cluster_id)
        self.fuel_web.run_ostf(
            cluster_id=cluster_id, test_sets=['ha', 'smoke', 'sanity'])
        self.env.make_snapshot("vcenter_vmdk_ha_stop_deployment")

    @test(depends_on=[SetupEnvironment.prepare_slaves_5],
          groups=["vcenter_vmdk_ha_deployment_with_cinder"])
    @log_snapshot_on_error
    def vcenter_vmdk_ha_deployment_with_cinder(self):
        """
        Scenario:
            1. Create cluster
            2. Add 4 nodes with roles:
               3 controller
               1 cinder
            3. Deploy cluster
            4. Check network connectivity and run osft
        """
        self.env.revert_snapshot("ready_with_5_slaves")
        ext_node_names = ['esxi1', 'esxi2', 'vcenter', 'trusty']
        self.fuel_web.workstation_revert_snapshot(ext_node_names)

        # Configure cluster
        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=settings.DEPLOYMENT_MODE_HA,
            settings={
                'use_vcenter': True,
                'volumes_lvm': False,
                'volumes_vmdk': True,
                'images_vcenter': settings.IMAGES_VCENTER,
                'host_ip': settings.VCENTER_IP,
                'vc_user': settings.VCENTER_USERNAME,
                'vc_password': settings.VCENTER_PASSWORD,
                'cluster': settings.VCENTER_CLUSTERS,
                'tenant': 'vcenter',
                'user': 'vcenter',
                'password': 'vcenter',
                'vc_datacenter': settings.VC_DATACENTER,
                'vc_datastore': settings.VC_DATASTORE,
                'vc_image_dir': settings.VC_IMAGE_DIR,
                'vc_host': settings.VC_HOST
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
        self.fuel_web.client.get_cluster(cluster_id)
        self.fuel_web.verify_network(cluster_id)
        self.fuel_web.run_ostf(
            cluster_id=cluster_id, test_sets=['ha', 'smoke', 'sanity'])
        self.env.make_snapshot("vcenter_vmdk_ha_deployment_with_cinder")

    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["vcenter_vmdk_simple_stop_deployment"])
    @log_snapshot_on_error
    def vcenter_vmdk_simple_stop_deployment(self):
        """
        Scenario:
            1. Create cluster
            2. Add 3 nodes with roles:
               1 controller + 1 cinder
               1 cinder
            3. stop deployment of OP
            4. wait until nodes will be 'online' again
            5. then re-deploy cluster again
            4. Check network connectivity and run osft
        """
        self.env.revert_snapshot("ready_with_3_slaves")
        ext_node_names = ['esxi1', 'esxi2', 'vcenter', 'trusty']
        self.fuel_web.workstation_revert_snapshot(ext_node_names)

        # Configure cluster
        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=settings.DEPLOYMENT_MODE_SIMPLE,
            settings={
                'use_vcenter': True,
                'volumes_lvm': False,
                'volumes_vmdk': True,
                'images_vcenter': settings.IMAGES_VCENTER,
                'host_ip': settings.VCENTER_IP,
                'vc_user': settings.VCENTER_USERNAME,
                'vc_password': settings.VCENTER_PASSWORD,
                'cluster': settings.VCENTER_CLUSTERS,
                'tenant': 'vcenter',
                'user': 'vcenter',
                'password': 'vcenter',
                'vc_datacenter': settings.VC_DATACENTER,
                'vc_datastore': settings.VC_DATASTORE,
                'vc_image_dir': settings.VC_IMAGE_DIR,
                'vc_host': settings.VC_HOST
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
        try:
                self.fuel_web.stop_deployment_wait(cluster_id)
        except Exception:
                    logger.debug(traceback.format_exc())
        self.fuel_web.wait_nodes_get_online_state(self.env.nodes().slaves[:2])
        self.fuel_web.deploy_cluster_wait(cluster_id)
        self.fuel_web.verify_network(cluster_id)
        self.fuel_web.run_ostf(
            cluster_id=cluster_id, test_sets=['smoke', 'sanity'])
        self.env.make_snapshot("vcenter_vmdk_simple_stop_deployment")
