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

from proboscis.asserts import assert_equal
from proboscis import test

from fuelweb_test import logger
from fuelweb_test.helpers.decorators import log_snapshot_on_error
from fuelweb_test import settings
from fuelweb_test.tests.base_test_case import SetupEnvironment
from fuelweb_test.tests.base_test_case import TestBasic


@test(groups=["nsx"])
class NsxTestsInSimpleMode(TestBasic):

    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["nsx_simple_stt"])
    @log_snapshot_on_error
    def nsx_simple_stt(self):
        """
        Deploy cluster in simple mode
           with Neutron NSX plugin
           with stt,
           with cinder storage

        Scenario:
            1. Create cluster
            2. Add 1 node with controller role
            3. Add 1 node with compute role
            4. Add 1 node with Cinder LVM
            5. Run network verification
            6. Run OSTF

        Snapshot nsx_simple_stt

        """
        self.env.revert_snapshot("ready_with_3_slaves")

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=settings.DEPLOYMENT_MODE_SIMPLE,
            settings={
                'net_provider': 'neutron',
                'net_l23_provider': 'nsx',
                'volumes_lvm': True,
                'volumes_vmdk': False,
                'nsx_plugin': True,
                'nsx_username': settings.NSX_USERNAME,
                'nsx_password': settings.NSX_PASSWORD,
                'transport_zone_uuid': settings.NSX_TRANSPORT_ZONE,
                'l3_gw_service_uuid': settings.L3_SERVICE_UUID,
                'nsx_controllers': settings.NSX_CONTROLLER_ENDPOINT,
                'packages_url': settings.URL_TO_NSX_BITS,
                'segmentation_type': 'gre',
                'connector_type': settings.NSX_CONNECTOR_TYPE
            }
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['compute'],
                'slave-03': ['ceph-osd']

            }
        )

        self.fuel_web.client.update_management_network_settings(cluster_id)
        self.fuel_web.deploy_cluster_wait(cluster_id)
        cluster = self.fuel_web.client.get_cluster(cluster_id)
        assert_equal(str(cluster['net_provider']), 'neutron')
        self.fuel_web.verify_network(cluster_id)
        self.fuel_web.run_ostf(cluster_id=cluster_id)
        self.env.make_snapshot("nsx_simple_stt")

    @test(depends_on=[SetupEnvironment.prepare_slaves_5],
          groups=["nsx_simple_stt_add_node"])
    @log_snapshot_on_error
    def nsx_simple_stt_add_node(self):

        """Deploy cluster in simple mode
           with Neutron NSX plugin with STT,
           with 1 controllers, 1 compute, 2 ceph osd,
           after deploy add one node and re-deploy again

        Scenario:
            1. Create cluster
            2. Add 1 node with controller role
            3. Add 1 node with compute role
            4. Add 2 nodes with Ceph-OSD
            5. Run deployment
            6. When deployment is finished
               add 1 node with 'Compute' role
            7. Re-deploy clusters again
            8. Run ostf and network verification

        Snapshot nsx_simple_stt_add_node

        """
        self.env.revert_snapshot("ready_with_5_slaves")

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=settings.DEPLOYMENT_MODE_SIMPLE,
            settings={
                'net_provider': 'neutron',
                'net_l23_provider': 'nsx',
                'volumes_lvm': True,
                'volumes_vmdk': False,
                'nsx_plugin': True,
                'nsx_username': settings.NSX_USERNAME,
                'nsx_password': settings.NSX_PASSWORD,
                'transport_zone_uuid': settings.NSX_TRANSPORT_ZONE,
                'l3_gw_service_uuid': settings.L3_SERVICE_UUID,
                'nsx_controllers': settings.NSX_CONTROLLER_ENDPOINT,
                'packages_url': settings.URL_TO_NSX_BITS,
                'segmentation_type': 'gre',
                'connector_type': settings.NSX_CONNECTOR_TYPE
            }

        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['compute'],
                'slave-03': ['ceph-osd'],
                'slave-04': ['ceph-osd']
            }
        )
        self.fuel_web.client.update_management_network_settings(cluster_id)
        self.fuel_web.deploy_cluster_wait(cluster_id)
        cluster = self.fuel_web.client.get_cluster(cluster_id)
        logger.info('The cluster id is %s', cluster)
        self.fuel_web.verify_network(cluster_id)
        self.fuel_web.update_nodes(
            cluster_id, {
                'slave-05': ['compute']
            }, True, False
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)
        cluster = self.fuel_web.client.get_cluster(cluster_id)
        logger.info('The cluster id is %s', cluster)
        self.fuel_web.verify_network(cluster_id)
        self.fuel_web.run_ostf(cluster_id=cluster_id)
        self.env.make_snapshot("nsx_simple_stt_add_node")

    @test(depends_on=[SetupEnvironment.prepare_slaves_5],
          groups=["nsx_simple_stt_stop_provisioning"])
    @log_snapshot_on_error
    def nsx_simple_stt_stop_provisioning(self):

            """
            Deploy cluster in simple mode
               with Neutron NSX plugin
               with STT,
               with cinder and ceph osd storages,
               stop on action provisioning and then start again

            Scenario:
                1. Create cluster
                2. Add 1 node with controller role
                3. Add 1 node with compute role
                4. Add 1 node with Cinder LVM
                5. Add 2 nodes with Ceph OSD
                6. Run provisioning task
                7. Stop deployment  task
                7.1 Wait when all nodes will be online
                8. Re-deploy cluster again
                9. Run network verification
                10. Run OSTF

            Snapshot nsx_simple_stt_stop_provisioning

            """
            self.env.revert_snapshot("ready_with_5_slaves")
            cluster_id = self.fuel_web.create_cluster(
                name=self.__class__.__name__,
                mode=settings.DEPLOYMENT_MODE_SIMPLE,
                settings={
                    'net_provider': 'neutron',
                    'net_l23_provider': 'nsx',
                    'volumes_lvm': True,
                    'volumes_vmdk': False,
                    'nsx_plugin': True,
                    'nsx_username': settings.NSX_USERNAME,
                    'nsx_password': settings.NSX_PASSWORD,
                    'transport_zone_uuid': settings.NSX_TRANSPORT_ZONE,
                    'l3_gw_service_uuid': settings.L3_SERVICE_UUID,
                    'nsx_controllers': settings.NSX_CONTROLLER_ENDPOINT,
                    'packages_url': settings.URL_TO_NSX_BITS,
                    'segmentation_type': 'gre',
                    'connector_type': settings.NSX_CONNECTOR_TYPE
                }
            )
            self.fuel_web.update_nodes(
                cluster_id,
                {
                    'slave-01': ['controller'],
                    'slave-02': ['compute'],
                    'slave-03': ['cinder'],
                    'slave-04': ['ceph-osd'],
                    'slave-05': ['ceph-osd']
                }
            )
            self.fuel_web.client.update_management_network_settings(cluster_id)
            self.fuel_web.provisioning_cluster_wait(
                cluster_id=cluster_id, progress=20)
            self.fuel_web.stop_deployment_wait(cluster_id)
            self.fuel_web.wait_nodes_get_online_state(
                self.env.nodes().slaves[:5])
            self.fuel_web.deploy_cluster_wait(cluster_id)
            cluster = self.fuel_web.client.get_cluster(cluster_id)
            logger.info('The cluster id is %s', cluster)
            self.fuel_web.verify_network(cluster_id)
            self.fuel_web.run_ostf(cluster_id=cluster_id)
            self.env.make_snapshot("nsx_simple_stt_stop_provisioning")

    @test(depends_on=[SetupEnvironment.prepare_slaves_5],
          groups=["nsx_simple_stt_restart_node"])
    @log_snapshot_on_error
    def nsx_simple_stt_restart_node(self):

            """
            Deploy cluster in simple mode
               with Neutron NSX plugin
               with STT,
               with ceph osd storages,
               deploy cluster, then  reset some node
               and then start it again

            Scenario:
                1. Create cluster
                2. Add 1 node with controller role
                3. Add 1 node with compute role
                4. Add 2 nodes with Ceph OSD
                5. Deploy cluster
                6. Reset some node
                7. Then start this node again
                8. Run network verification
                9. Run OSTF

            Snapshot nsx_simple_stt_restart_node

            """
            self.env.revert_snapshot("ready_with_5_slaves")

            cluster_id = self.fuel_web.create_cluster(
                name=self.__class__.__name__,
                mode=settings.DEPLOYMENT_MODE_SIMPLE,
                settings={
                    'net_provider': 'neutron',
                    'net_l23_provider': 'nsx',
                    'volumes_lvm': True,
                    'volumes_vmdk': False,
                    'nsx_plugin': True,
                    'nsx_username': settings.NSX_USERNAME,
                    'nsx_password': settings.NSX_PASSWORD,
                    'transport_zone_uuid': settings.NSX_TRANSPORT_ZONE,
                    'l3_gw_service_uuid': settings.L3_SERVICE_UUID,
                    'nsx_controllers': settings.NSX_CONTROLLER_ENDPOINT,
                    'packages_url': settings.URL_TO_NSX_BITS,
                    'segmentation_type': 'gre',
                    'connector_type': settings.NSX_CONNECTOR_TYPE
                }

            )
            self.fuel_web.update_nodes(
                cluster_id,
                {
                    'slave-01': ['controller'],
                    'slave-02': ['compute'],
                    'slave-03': ['ceph-osd'],
                    'slave-04': ['ceph-osd']
                }
            )
            self.fuel_web.client.update_management_network_settings(cluster_id)
            self.fuel_web.deploy_cluster_wait_progress(cluster_id, progress=30)
            self.fuel_web.warm_restart_nodes(self.env.nodes().slaves[3])
            self.fuel_web.wait_nodes_get_online_state(
                self.env.nodes().slaves[:4])
            self.fuel_web.deploy_cluster_wait_progress(cluster_id,
                                                       progress=100)
            self.fuel_web.verify_network(cluster_id)
            self.fuel_web.run_ostf(cluster_id=cluster_id)
            self.env.make_snapshot("nsx_simple_stt_restart_node")

    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["nsx_simple_gre_add_node"])
    @log_snapshot_on_error
    def nsx_simple_gre_add_node(self):

        """Deploy cluster in simple mode
           with Neutron NSX plugin with GRE,
           with 1 controller and 1 compute,
           deploy cluster,
           then add one more compute node
           re-deploy cluster again

        Scenario:
            1. Create cluster
            2. Add 1 node with controller role
            3. Add 1 node with compute role
            4. Deploy cluster
            5. Validate cluster was set up correctly, there are no dead
            services, there are no errors in logs
            6. Add 1 more compute role
            7. Re-deploy cluster again
            8. Run network verification
            9. Run OSTF

        Snapshot nsx_simple_gre_add_node

        """
        self.env.revert_snapshot("ready_with_3_slaves")

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=settings.DEPLOYMENT_MODE_SIMPLE,
            settings={
                'net_provider': 'neutron',
                'net_l23_provider': 'nsx',
                'volumes_lvm': True,
                'volumes_vmdk': False,
                'nsx_plugin': True,
                'nsx_username': settings.NSX_USERNAME,
                'nsx_password': settings.NSX_PASSWORD,
                'transport_zone_uuid': settings.NSX_TRANSPORT_ZONE,
                'l3_gw_service_uuid': settings.L3_SERVICE_UUID,
                'nsx_controllers': settings.NSX_CONTROLLER_ENDPOINT,
                'packages_url': settings.URL_TO_NSX_BITS,
                'segmentation_type': 'gre',
                'connector_type': settings.NSX_CONNECTOR_TYPE
            }
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['compute']
            }
        )
        self.fuel_web.client.update_management_network_settings(cluster_id)
        self.fuel_web.deploy_cluster_wait(cluster_id)
        cluster = self.fuel_web.client.get_cluster(cluster_id)
        logger.info('The cluster id is %s', cluster)
        self.fuel_web.update_nodes(
            cluster_id, {
                'slave-03': ['compute']
            }, True, False
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)
        cluster = self.fuel_web.client.get_cluster(cluster_id)
        logger.info('The cluster id is %s', cluster)
        self.fuel_web.verify_network(cluster_id)
        self.fuel_web.run_ostf(cluster_id=cluster_id)
        self.env.make_snapshot("nsx_simple_gre_add_node")

    @test(depends_on=[SetupEnvironment.prepare_slaves_5],
          groups=["nsx_simple_gre_stop_deployment"])
    @log_snapshot_on_error
    def nsx_simple_gre_stop_deployment(self):

        """
        Deploy cluster in simple mode
               with Neutron NSX plugin
               with gre,
               with roles: 1 controller, 1 compute and  3 ceph osd storages,
               stop on deploy and then start it again

        Scenario:
                1. Create cluster
                2. Add 1 node with controller role
                3. Add 1 node with compute role
                4. Add 3 nodes with Ceph OSD
                5. Run provisioning task
                6. Stop deployment  task
                7. Remove one node and re-deploy cluster again
                8. Run network verification
                9. Run OSTF

        Snapshot nsx_simple_gre_stop_deployment

        """
        self.env.revert_snapshot("ready_with_5_slaves")

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=settings.DEPLOYMENT_MODE_SIMPLE,
            settings={
                'net_provider': 'neutron',
                'net_l23_provider': 'nsx',
                'volumes_lvm': True,
                'volumes_vmdk': False,
                'nsx_plugin': True,
                'nsx_username': settings.NSX_USERNAME,
                'nsx_password': settings.NSX_PASSWORD,
                'transport_zone_uuid': settings.NSX_TRANSPORT_ZONE,
                'l3_gw_service_uuid': settings.L3_SERVICE_UUID,
                'nsx_controllers': settings.NSX_CONTROLLER_ENDPOINT,
                'packages_url': settings.URL_TO_NSX_BITS,
                'segmentation_type': 'gre',
                'connector_type': settings.NSX_CONNECTOR_TYPE
            }
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['compute'],
                'slave-03': ['ceph-osd'],
                'slave-04': ['ceph-osd'],
                'slave-05': ['ceph-osd']
            }
        )
        self.fuel_web.client.update_management_network_settings(cluster_id)
        self.fuel_web.provisioning_cluster_wait(cluster_id)
        self.fuel_web.deploy_task_wait(cluster_id=cluster_id, progress=60)
        self.fuel_web.stop_deployment_wait(cluster_id)
        self.fuel_web.wait_nodes_get_online_state(self.env.nodes().slaves[:5])
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-03': ['ceph-osd'],
            }, False, True
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)
        cluster = self.fuel_web.client.get_cluster(cluster_id)
        logger.info('The cluster id is %s', cluster)
        self.fuel_web.verify_network(cluster_id)
        self.fuel_web.run_ostf(cluster_id=cluster_id)
        self.env.make_snapshot("nsx_simple_gre_stop_deployment")

    @test(depends_on=[SetupEnvironment.prepare_slaves_5],
          groups=["nsx_simple_stt_add_one_node_and_delete"])
    @log_snapshot_on_error
    def nsx_simple_stt_add_one_node_and_delete(self):

        """
           Deploy cluster in simple mode
           with Neutron NSX plugin
           with stt,
           after deploy add one node with new role
           and delete one node with another role
           then re-deploy env again

        Scenario:
            1. Create cluster
            2. Add 1 node with roles: 'controller+ceph-osd'
            3. Add 1 node with 'compute' role
            4. Deploy cluster
            5. Run network verification
            6. Run OSTF
            7.
            8. Add one node with 'compute-ceph-osd-role' role
               and delete one node with 'compute' role
            9. Re-deploy cluster again
            10. Run network verification
            11. Run OSTF

        Snapshot nsx_simple_stt_add_one_node_and_delete
        """
        self.env.revert_snapshot("ready_with_5_slaves")

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=settings.DEPLOYMENT_MODE_SIMPLE,
            settings={
                'net_provider': 'neutron',
                'net_l23_provider': 'nsx',
                'volumes_lvm': True,
                'volumes_vmdk': False,
                'nsx_plugin': True,
                'nsx_username': settings.NSX_USERNAME,
                'nsx_password': settings.NSX_PASSWORD,
                'transport_zone_uuid': settings.NSX_TRANSPORT_ZONE,
                'l3_gw_service_uuid': settings.L3_SERVICE_UUID,
                'nsx_controllers': settings.NSX_CONTROLLER_ENDPOINT,
                'packages_url': settings.URL_TO_NSX_BITS,
                'segmentation_type': 'gre',
                'connector_type': settings.NSX_CONNECTOR_TYPE
            }
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller', 'ceph-osd'],
                'slave-02': ['compute'],
            }
        )
        self.fuel_web.client.update_management_network_settings(cluster_id)
        self.fuel_web.deploy_cluster_wait(cluster_id)
        cluster = self.fuel_web.client.get_cluster(cluster_id)
        logger.info('The cluster id is %s', cluster)
        self.fuel_web.verify_network(cluster_id)
        self.fuel_web.run_ostf(cluster_id)
        self.fuel_web.update_nodes(
            cluster_id, {
                'slave-03': ['compute', 'ceph-osd'],
                'slave-02': ['compute']
            }, True, True
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)
        cluster = self.fuel_web.client.get_cluster(cluster_id)
        logger.info('The cluster id is %s', cluster)
        self.fuel_web.verify_network(cluster_id)
        self.fuel_web.run_ostf(cluster_id=cluster_id)
        self.env.make_snapshot("nsx_simple_stt_add_one_node_and_delete")

    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["nsx_simple_ipsec_gre"])
    @log_snapshot_on_error
    def nsx_simple_ipsec_gre(self):
        """
        Deploy cluster in simple mode,
           with Neutron NSX plugin,
           with GRE over IPSec,
           with cinder storage

        Scenario:
            1. Create cluster
            2. Add 1 node with controller role
            3. Add 1 node with compute role
            4. Add 1 node with Cinder LVM
            5. Run network verification
            6. Run OSTF

        Snapshot nsx_simple_ipsec_gre

        """
        self.env.revert_snapshot("ready_with_3_slaves")

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=settings.DEPLOYMENT_MODE_SIMPLE,
            settings={
                'net_provider': 'neutron',
                'net_l23_provider': 'nsx',
                'volumes_lvm': True,
                'volumes_vmdk': False,
                'nsx_plugin': True,
                'nsx_username': settings.NSX_USERNAME,
                'nsx_password': settings.NSX_PASSWORD,
                'transport_zone_uuid': settings.NSX_TRANSPORT_ZONE,
                'l3_gw_service_uuid': settings.L3_SERVICE_UUID,
                'nsx_controllers': settings.NSX_CONTROLLER_ENDPOINT,
                'packages_url': settings.URL_TO_NSX_BITS,
                'segmentation_type': 'gre',
                'connector_type': settings.NSX_CONNECTOR_TYPE
            }
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['compute'],
                'slave-03': ['ceph-osd']

            }
        )

        self.fuel_web.client.update_management_network_settings(cluster_id)
        self.fuel_web.deploy_cluster_wait(cluster_id)
        cluster = self.fuel_web.client.get_cluster(cluster_id)
        assert_equal(str(cluster['net_provider']), 'neutron')
        self.fuel_web.verify_network(cluster_id)
        self.fuel_web.run_ostf(cluster_id=cluster_id)
        self.env.make_snapshot("nsx_simple_ipsec_gre")

    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["nsx_simple_ipsec_stt"])
    @log_snapshot_on_error
    def nsx_simple_ipsec_stt(self):
        """
        Deploy cluster in simple mode,
           with Neutron NSX plugin,
           with STT over IPSec,
           with cinder storage

        Scenario:
            1. Create cluster
            2. Add 1 node with controller role
            3. Add 1 node with compute role
            4. Add 1 node with Cinder LVM
            5. Run network verification
            6. Run OSTF

        Snapshot nsx_simple_ipsec_stt

        """
        self.env.revert_snapshot("ready_with_3_slaves")

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=settings.DEPLOYMENT_MODE_SIMPLE,
            settings={
                'net_provider': 'neutron',
                'net_l23_provider': 'nsx',
                'volumes_lvm': True,
                'volumes_vmdk': False,
                'nsx_plugin': True,
                'nsx_username': settings.NSX_USERNAME,
                'nsx_password': settings.NSX_PASSWORD,
                'transport_zone_uuid': settings.NSX_TRANSPORT_ZONE,
                'l3_gw_service_uuid': settings.L3_SERVICE_UUID,
                'nsx_controllers': settings.NSX_CONTROLLER_ENDPOINT,
                'packages_url': settings.URL_TO_NSX_BITS,
                'segmentation_type': 'gre',
                'connector_type': settings.NSX_CONNECTOR_TYPE
            }
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['compute'],
                'slave-03': ['ceph-osd']

            }
        )

        self.fuel_web.client.update_management_network_settings(cluster_id)
        self.fuel_web.deploy_cluster_wait(cluster_id)
        cluster = self.fuel_web.client.get_cluster(cluster_id)
        assert_equal(str(cluster['net_provider']), 'neutron')
        self.fuel_web.verify_network(cluster_id)
        self.fuel_web.run_ostf(cluster_id=cluster_id)
        self.env.make_snapshot("nsx_simple_ipsec_stt")

    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["nsx_simple_bridge"])
    @log_snapshot_on_error
    def nsx_simple_bridge(self):
        """
        Deploy cluster in simple mode,
           with Neutron NSX plugin,
           with Bridge,
           with cinder storage

        Scenario:
            1. Create cluster
            2. Add 1 node with controller role
            3. Add 1 node with compute role
            4. Add 1 node with Cinder LVM
            5. Run network verification
            6. Run OSTF

        Snapshot nsx_simple_bridge

        """
        self.env.revert_snapshot("ready_with_3_slaves")

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=settings.DEPLOYMENT_MODE_SIMPLE,
            settings={
                'net_provider': 'neutron',
                'net_l23_provider': 'nsx',
                'volumes_lvm': True,
                'volumes_vmdk': False,
                'nsx_plugin': True,
                'nsx_username': settings.NSX_USERNAME,
                'nsx_password': settings.NSX_PASSWORD,
                'transport_zone_uuid': settings.NSX_TRANSPORT_ZONE,
                'l3_gw_service_uuid': settings.L3_SERVICE_UUID,
                'nsx_controllers': settings.NSX_CONTROLLER_ENDPOINT,
                'packages_url': settings.URL_TO_NSX_BITS,
                'segmentation_type': 'gre',
                'connector_type': settings.NSX_CONNECTOR_TYPE
            }
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['compute'],
                'slave-03': ['ceph-osd']

            }
        )

        self.fuel_web.client.update_management_network_settings(cluster_id)
        self.fuel_web.deploy_cluster_wait(cluster_id)
        cluster = self.fuel_web.client.get_cluster(cluster_id)
        assert_equal(str(cluster['net_provider']), 'neutron')
        self.fuel_web.verify_network(cluster_id)
        self.fuel_web.run_ostf(cluster_id=cluster_id)
        self.env.make_snapshot("nsx_simple_bridge")
