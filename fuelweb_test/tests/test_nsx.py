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

from fuelweb_test import logger
from fuelweb_test.helpers.decorators import log_snapshot_on_error
from fuelweb_test import settings
from fuelweb_test.tests.base_test_case import SetupEnvironment
from fuelweb_test.tests.base_test_case import TestBasic

from proboscis import test


@test(groups=["nsx"])
class NsxTestsInSimpleMode(TestBasic):

    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["deploy_simple_nsx_stt"])
    @log_snapshot_on_error
    def deploy_simple_nsx_stt(self):

        """
        Deploy cluster in simple mode
           with Neutron NSX plugin
           with stt,
           with cinder storage

        Scenario:
            1. Create cluster
            2. Add 1 node with controller role
            3. Add 1 node with compute role
            4. Add 1 role with Cinder LVM
            5. Run network verification
            6. Run OSTF

        Snapshot deploy_simple_nsx_stt

        """
        self.env.revert_snapshot("ready_with_3_slaves")

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=settings.DEPLOYMENT_MODE_SIMPLE,
            settings={
                'net_provider': 'neutron-nsx',
                'volumes_lvm': True,
                'nsx_plugin': True,
                'nsx_username': settings.NSX_USERNAME,
                'nsx_password': settings.NSX_PASSWORD,
                'transport_zone_uuid': settings.NSX_TRANSPORT_ZONE,
                'l3_gw_service_uuid': settings.L3_SERVICE_UUID,
                'nsx_controllers': settings.NSX_CONTROLLER_ENDPOINT,
                'packages_url': settings.URL_TO_NSX_BITS,
                'connector_type': 'stt'
            }

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
        self.fuel_web.client.get_cluster(cluster_id)
        self.fuel_web.verify_network(cluster_id)
        self.fuel_web.run_ostf(cluster_id=cluster_id)
        self.env.make_snapshot("deploy_simple_nsx_stt")

    @test(depends_on=[SetupEnvironment.prepare_slaves_5],
          groups=["deploy_simple_nsx_stt_add_node"])
    @log_snapshot_on_error
    def deploy_simple_nsx_stt_add_node(self):

        """Deploy cluster in simple mode
           with Neutron NSX plugin with STT,
           with 1 controllers, 1 compute, 2 ceph osd,
           after deploy add one node and re-deploy again

        Scenario:
            1. Create cluster
            2. Add 1 node with controller role
            3. Add 1 node with compute role
            4. Add 2 role with Ceph-OSD
            5. Run deployment
            6. When deployment is finished
               add 1 node with 'Compute' role
            7. Re-deploy cluster again
            8. Run ostf anf network verification

        Snapshot deploy_simple_nsx_stt_add_node

        """
        self.env.revert_snapshot("ready_with_5_slaves")

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=settings.DEPLOYMENT_MODE_SIMPLE,
            settings={
                'net_provider': 'neutron-nsx',
                'images_ceph': True,
                'volumes_ceph': True,
                'nsx_plugin': True,
                'nsx_username': settings.NSX_USERNAME,
                'nsx_password': settings.NSX_PASSWORD,
                'transport_zone_uuid': settings.NSX_TRANSPORT_ZONE,
                'l3_gw_service_uuid': settings.L3_SERVICE_UUID,
                'nsx_controllers': settings.NSX_CONTROLLER_ENDPOINT,
                'packages_url': settings.URL_TO_NSX_BITS,
                'connector_type': 'stt'
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
        self.fuel_web.deploy_cluster_wait(cluster_id)
        self.fuel_web.verify_network(cluster_id)
        self.fuel_web.update_nodes(
            cluster_id, {
                'slave-05': ['compute']
            }, True, False
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)
        self.fuel_web.verify_network(cluster_id)
        self.fuel_web.run_ostf(cluster_id=cluster_id)
        self.env.make_snapshot("deploy_simple_nsx_stt_add_node")

    @test(depends_on=[SetupEnvironment.prepare_slaves_5],
          groups=["deploy_nsx_simple_stt_stop_provisioning"])
    @log_snapshot_on_error
    def deploy_nsx_simple_stt_stop_provisioning(self):

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
                4. Add 1 role with Cinder LVM
                5. Add 2 roles with Ceph OSD
                6. Run provisioning task
                7. Stop deployment  task
                8. Re-deploy cluster
                9. Run network verification
                10. Run OSTF

            Snapshot deploy_nsx_simple_stt_stop_provisioning

            """
            self.env.revert_snapshot("ready_with_5_slaves")
            cluster_id = self.fuel_web.create_cluster(
                name=self.__class__.__name__,
                mode=settings.DEPLOYMENT_MODE_SIMPLE,
                settings={'net_provider': 'neutron-nsx',
                          'images_ceph': True,
                          'volumes_lvm': True,
                          'nsx_plugin': True,
                          'nsx_username': settings.NSX_USERNAME,
                          'nsx_password': settings.NSX_PASSWORD,
                          'transport_zone_uuid': settings.NSX_TRANSPORT_ZONE,
                          'l3_gw_service_uuid': settings.L3_SERVICE_UUID,
                          'nsx_controllers': settings.NSX_CONTROLLER_ENDPOINT,
                          'packages_url': settings.URL_TO_NSX_BITS,
                          'connector_type': 'stt'
                          }
            )
            self.fuel_web.update_nodes(
                cluster_id,
                {'slave-01': ['controller'],
                 'slave-02': ['compute'],
                 'slave-03': ['cinder'],
                 'slave-04': ['ceph-osd'],
                 'slave-05': ['ceph-osd']}
            )
            self.fuel_web.provisioning_cluster_wait(
                cluster_id=cluster_id, progress=20)
            try:
                self.fuel_web.stop_deployment_wait(cluster_id)
            except Exception:
                logger.debug(traceback.format_exc())
            self.fuel_web.wait_nodes_get_online_state(
                self.env.nodes().slaves[:2])
            self.fuel_web.deploy_cluster_wait(cluster_id)
            self.fuel_web.client.get_cluster(cluster_id)
            self.fuel_web.verify_network(cluster_id)
            self.fuel_web.run_ostf(cluster_id=cluster_id,
                                   test_sets=['smoke', 'sanity'])
            self.env.make_snapshot("deploy_nsx_simple_stt_stop_provisioning")

    @test(depends_on=[SetupEnvironment.prepare_slaves_5],
          groups=["deploy_nsx_simple_stt_restart_node"])
    @log_snapshot_on_error
    def deploy_nsx_simple_stt_restart_node(self):

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
                4. Add 2 roles with Ceph OSD
                5. Deploy cluster
                6. Reset some node
                7. Then start this node again
                8. Run network verification
                9. Run OSTF

            Snapshot deploy_nsx_simple_stt_restart_node

            """
            self.env.revert_snapshot("ready_with_5_slaves")

            cluster_id = self.fuel_web.create_cluster(
                name=self.__class__.__name__,
                mode=settings.DEPLOYMENT_MODE_SIMPLE,
                settings={
                    'net_provider': 'neutron-nsx',
                    'volumes_ceph': True,
                    'images_ceph': True,
                    'nsx_plugin': True,
                    'nsx_username': settings.NSX_USERNAME,
                    'nsx_password': settings.NSX_PASSWORD,
                    'transport_zone_uuid': settings.NSX_TRANSPORT_ZONE,
                    'l3_gw_service_uuid': settings.L3_SERVICE_UUID,
                    'nsx_controllers': settings.NSX_CONTROLLER_ENDPOINT,
                    'packages_url': settings.URL_TO_NSX_BITS,
                    'connector_type': 'stt'
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

            self.fuel_web.during_deployment_restart_node(
                cluster_id, self.env.nodes().slaves[3], progress_value=30)
            self.fuel_web.verify_network(cluster_id)
            self.fuel_web.run_ostf(cluster_id=cluster_id)
            self.env.make_snapshot("deploy_nsx_simple_stt_restart_node")

    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["deploy_nsx_simple_gre_add_node"])
    @log_snapshot_on_error
    def deploy_nsx_simple_gre_add_node(self):

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
            4.1 Validate cluster was set up correctly, there are no dead
            services, there are no errors in logs
            5. Add 1 more compute role
            6. Re-deploy cluster again
            7. Run network verification
            8. Run OSTF

        Snapshot deploy_nsx_simple_gre_add_node

        """
        self.env.revert_snapshot("ready_with_3_slaves")

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=settings.DEPLOYMENT_MODE_SIMPLE,
            settings={
                'net_provider': 'neutron-nsx',
                'nsx_plugin': True,
                'nsx_username': settings.NSX_USERNAME,
                'nsx_password': settings.NSX_PASSWORD,
                'transport_zone_uuid': settings.NSX_TRANSPORT_ZONE,
                'l3_gw_service_uuid': settings.L3_SERVICE_UUID,
                'nsx_controllers': settings.NSX_CONTROLLER_ENDPOINT,
                'packages_url': settings.URL_TO_NSX_BITS,
                'connector_type': 'gre'
            }

        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['compute'],
            }
        )

        self.fuel_web.deploy_cluster_wait(cluster_id)
        self.fuel_web.client.get_cluster(cluster_id)
        self.fuel_web.assert_cluster_ready(
            'slave-01', smiles_count=4, timeout=300)
        self.fuel_web.update_nodes(
            cluster_id, {
                'slave-03': ['compute']
            }, True, False
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)
        self.fuel_web.verify_network(cluster_id)
        self.fuel_web.run_ostf(cluster_id=cluster_id)
        self.env.make_snapshot("deploy_nsx_simple_gre_add_node")

    @test(depends_on=[SetupEnvironment.prepare_slaves_5],
          groups=["deploy_nsx_simple_gre_stop_deployment"])
    @log_snapshot_on_error
    def deploy_nsx_simple_gre_stop_deployment(self):

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
                4. Add 3 roles with Ceph OSD
                5. Run provisioning task
                6. Stop deployment  task
                7. Re-deploy cluster
                8. Run network verification
                9. Run OSTF

        Snapshot deploy_nsx_simple_gre_stop_deployment

        """
        self.env.revert_snapshot("ready_with_5_slaves")

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=settings.DEPLOYMENT_MODE_SIMPLE,
            settings={'net_provider': 'neutron-nsx',
                      'volumes_ceph': True,
                      'images_ceph': True,
                      'nsx_plugin': True,
                      'nsx_username': settings.NSX_USERNAME,
                      'nsx_password': settings.NSX_PASSWORD,
                      'transport_zone_uuid': settings.NSX_TRANSPORT_ZONE,
                      'l3_gw_service_uuid': settings.L3_SERVICE_UUID,
                      'nsx_controllers': settings.NSX_CONTROLLER_ENDPOINT,
                      'packages_url': settings.URL_TO_NSX_BITS,
                      'connector_type': 'gre'
                      }
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {'slave-01': ['controller'],
             'slave-02': ['compute'],
             'slave-03': ['ceph-osd'],
             'slave-04': ['ceph-osd'],
             'slave-05': ['ceph-osd']}
        )

        self.fuel_web.provisioning_cluster_wait(cluster_id)
        self.fuel_web.deploy_task_wait(cluster_id=cluster_id, progress=60)
        try:
            self.fuel_web.stop_deployment_wait(cluster_id)
        except Exception:
            logger.debug(traceback.format_exc())

        self.fuel_web.wait_nodes_get_online_state(self.env.nodes().slaves[:5])
        self.fuel_web.deploy_cluster_wait(cluster_id)
        self.fuel_web.verify_network(cluster_id)
        self.fuel_web.run_ostf(cluster_id=cluster_id)
        self.env.make_snapshot("deploy_nsx_simple_gre_stop_deployment")

    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["deploy_nsx_simple_gre_add_one_node"])
    @log_snapshot_on_error
    def deploy_nsx_simple_gre_add_one_node(self):

        """Deploy cluster in simple mode
           with Neutron NSX plugin
           with gre,
           add after deploy one node and re-deploy again

        Scenario:
            1. Create cluster
            2. Add 1 node with controller role
            3. Add 1 node with compute role
            4. Deploy cluster
            5. Run network verification
            6. Run OSTF
            7. Add one node
            8. Re-deploy cluster again
            9. Run network verification
            10. Run OSTF

        Snapshot nsx_simple_gre_add_one_node_conf2

        """
        self.env.revert_snapshot("ready_with_3_slaves")

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=settings.DEPLOYMENT_MODE_SIMPLE,
            settings={
                'net_provider': 'neutron-nsx',
                'nsx_plugin': True,
                'nsx_username': settings.NSX_USERNAME,
                'nsx_password': settings.NSX_PASSWORD,
                'transport_zone_uuid': settings.NSX_TRANSPORT_ZONE,
                'l3_gw_service_uuid': settings.L3_SERVICE_UUID,
                'nsx_controllers': settings.NSX_CONTROLLER_ENDPOINT,
                'packages_url': settings.URL_TO_NSX_BITS,
                'connector_type': 'gre'
            }

        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['compute'],
            }
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)
        self.fuel_web.client.get_cluster(cluster_id)
        self.fuel_web.verify_network(cluster_id)
        self.fuel_web.run_ostf(cluster_id=cluster_id)
        self.fuel_web.update_nodes(
            cluster_id, {
                'slave-03': ['compute']
            }, True, False
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)
        self.fuel_web.verify_network(cluster_id)
        self.fuel_web.run_ostf(cluster_id)
        self.env.make_snapshot("deploy_nsx_simple_gre_add_one_node")

    @test(depends_on=[SetupEnvironment.prepare_slaves_5],
          groups=["deploy_nsx_simple_stt_add_one_node_and_delete"])
    @log_snapshot_on_error
    def deploy_nsx_simple_stt_add_one_node_and_delete(self):

        """
           Deploy cluster in simple mode
           with Neutron NSX plugin
           with stt,
           after deploy add one node with 'controller' role
           and delete one node with 'controller' role (non primary controller)
           then re-deploy env again

        Scenario:
            1. Create cluster
            2. Add 2 node with roles: 'controller+ceph-osd'
            3. Add 1 node with 'compute' role
            4. Add 1 node with 'ceph-osd' role
            5. Deploy cluster
            6. Run network verification
            7. Run OSTF
            8. Add one node with 'controller' role
               and delete one node with 'controller' role
               (non primary).it must be simultaneously.
            9. Re-deploy cluster again
            10. Run network verification
            11. Run OSTF

        Snapshot deploy_nsx_simple_stt_add_one_node_and_delete
        """
        self.env.revert_snapshot("ready_with_5_slaves")

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=settings.DEPLOYMENT_MODE_SIMPLE,
            settings={
                'net_provider': 'neutron-nsx',
                'volumes_ceph': True,
                'images_ceph': True,
                'nsx_plugin': True,
                'nsx_username': settings.NSX_USERNAME,
                'nsx_password': settings.NSX_PASSWORD,
                'transport_zone_uuid': settings.NSX_TRANSPORT_ZONE,
                'l3_gw_service_uuid': settings.L3_SERVICE_UUID,
                'nsx_controllers': settings.NSX_CONTROLLER_ENDPOINT,
                'packages_url': settings.URL_TO_NSX_BITS,
                'connector_type': 'stt'
            }

        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller', 'ceph-osd'],
                'slave-02': ['controller', 'ceph-osd'],
                'slave-03': ['compute'],
                'slave-04': ['ceph-osd'],
            }
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)
        self.fuel_web.client.get_cluster(cluster_id)
        self.fuel_web.verify_network(cluster_id)
        self.fuel_web.run_ostf(cluster_id)
        self.fuel_web.update_nodes(
            cluster_id, {
                'slave-05': ['compute'],
                'slave-02': ['controller', 'ceph-osd'],
            }, True, True
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)
        self.fuel_web.verify_network(cluster_id)
        self.fuel_web.run_ostf(cluster_id=cluster_id)
        self.env.make_snapshot("deploy_nsx_simple_stt_add_one_node_and_delete")


@test(groups=["nsx"])
class NSXTestsInHAMode(TestBasic):

    @test(depends_on=[SetupEnvironment.prepare_slaves_7],
          groups=["deploy_nsx_HA_stt_stop_provisioning"])
    @log_snapshot_on_error
    def deploy_nsx_HA_stt_stop_provisioning(self):

        """Deploy cluster in HA mode
           with Neutron NSX plugin with STT,
           with 3 controllers, 1 compute, 3 ceph osd,
           stop on action provisioning and then start again

        Scenario:
            1. Create cluster
            2. Add 3 node with controller role
            3. Add 1 node with compute role
            4. Add 3 role with Ceph-OSD
            5. Run provisioning task
        (
        start provisioning-> stop deploy -> start deploy
        To implementation of this check we update 'deploy_cluster_wait'
        method and reduce interval of deployment, then we try - catch exception
        and stop deploy forcibly,
        for re-deploy we use settings for deploy cluster method
        )
            6. Stop deployment  task
            7. Re-deploy cluster
            8. Run network verification
            9. Run OSTF

        Snapshot deploy_nsx_HA_stt_stop_provisioning

        """
        self.env.revert_snapshot("ready_with_7_slaves")

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=settings.DEPLOYMENT_MODE_HA,
            settings={
                'net_provider': 'neutron-nsx',
                'volumes_ceph': True,
                'images_ceph': True,
                'nsx_plugin': True,
                'nsx_username': settings.NSX_USERNAME,
                'nsx_password': settings.NSX_PASSWORD,
                'transport_zone_uuid': settings.NSX_TRANSPORT_ZONE,
                'l3_gw_service_uuid': settings.L3_SERVICE_UUID,
                'nsx_controllers': settings.NSX_CONTROLLER_ENDPOINT,
                'packages_url': settings.URL_TO_NSX_BITS,
                'connector_type': 'stt'
            }

        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['controller'],
                'slave-03': ['controller'],
                'slave-04': ['compute'],
                'slave-05': ['ceph-osd'],
                'slave-06': ['ceph-osd'],
                'slave-07': ['ceph-osd']
            }
        )
        self.fuel_web.provisioning_cluster_wait(
            cluster_id=cluster_id, progress=20)
        try:
                self.fuel_web.stop_deployment_wait(cluster_id)
        except Exception:
                logger.debug(traceback.format_exc())
        self.fuel_web.wait_nodes_get_online_state(
            self.env.nodes().slaves[:7])
        self.fuel_web.deploy_cluster_wait(cluster_id)
        self.fuel_web.client.get_cluster(cluster_id)
        self.fuel_web.verify_network(cluster_id)
        self.fuel_web.run_ostf(cluster_id=cluster_id,
                               test_sets=['smoke', 'sanity'])
        self.env.make_snapshot("deploy_nsx_HA_stt_stop_provisioning")

    @test(depends_on=[SetupEnvironment.prepare_slaves_5],
          groups=["deploy_nsx_HA_stt_reset_node"])
    @log_snapshot_on_error
    def deploy_nsx_HA_stt_reset_node(self):

            """Deploy cluster in HA mode
               with Neutron NSX plugin with STT,
               with 2 controllers and 1 compute,
               with 1 Cinder LVM and 1 Ceph-OSD
               deploy cluster,
               then  reset some node and start it again
               re-deploy cluster again

            Scenario:
                1. Create cluster
                2. Add 2 nodes with controller roles
                3. Add 1 node with compute role
                4. Add 1 node with cinder LVM role
                5. Add 1 node with ceph osd  role
                6. Deploy cluster
                7. Reset some node
                8. Then start this node again
                9. Run network verification
               10. Run OSTF

            Snapshot deploy_nsx_HA_stt_reset_node

            """
            self.env.revert_snapshot("ready_with_5_slaves")

            cluster_id = self.fuel_web.create_cluster(
                name=self.__class__.__name__,
                mode=settings.DEPLOYMENT_MODE_HA,
                settings={
                    'net_provider': 'neutron-nsx',
                    'images_ceph': True,
                    'volumes_lvm': True,
                    'nsx_plugin': True,
                    'nsx_username': settings.NSX_USERNAME,
                    'nsx_password': settings.NSX_PASSWORD,
                    'transport_zone_uuid': settings.NSX_TRANSPORT_ZONE,
                    'l3_gw_service_uuid': settings.L3_SERVICE_UUID,
                    'nsx_controllers': settings.NSX_CONTROLLER_ENDPOINT,
                    'packages_url': settings.URL_TO_NSX_BITS,
                    'connector_type': 'stt'
                }

            )
            self.fuel_web.update_nodes(
                cluster_id,
                {
                    'slave-01': ['controller'],
                    'slave-02': ['controller'],
                    'slave-03': ['compute'],
                    'slave-04': ['ceph-osd'],
                    'slave-05': ['cinder', 'ceph-osd']
                }

            )
            self.fuel_web.during_deployment_restart_node(
                cluster_id, self.env.nodes().slaves[3], progress_value=60)
            self.fuel_web.verify_network(cluster_id)
            self.fuel_web.run_ostf(cluster_id=cluster_id)
            self.env.make_snapshot("deploy_nsx_HA_stt_reset_node")

    @test(depends_on=[SetupEnvironment.prepare_slaves_5],
          groups=["deploy_nsx_HA_stt_stop_deployment"])
    @log_snapshot_on_error
    def deploy_nsx_HA_stt_stop_deployment(self):

            """Deploy cluster in HA mode
               with Neutron NSX plugin with STT,
               with 3 controllers and 1 compute, with 1 Cinder LVM
               deploy cluster,
               then  stop deploy
               then start it again

            Scenario:
                1. Create cluster
                2. Add 3 nodes with controller roles
                3. Add 1 node with compute role
                4. Add 1 node with cinder LVM role
                5. Run provisioning task
                6. Stop deployment  task
                7. Re-deploy cluster
                8. Run network verification
                9. Run OSTFF

            Snapshot deploy_nsx_HA_stt_stop_deployment

            """

            self.env.revert_snapshot("ready_with_5_slaves")

            cluster_id = self.fuel_web.create_cluster(
                name=self.__class__.__name__,
                mode=settings.DEPLOYMENT_MODE_HA,
                settings={
                    'net_provider': 'neutron-nsx',
                    'volumes_lvm': True,
                    'nsx_plugin': True,
                    'nsx_username': settings.NSX_USERNAME,
                    'nsx_password': settings.NSX_PASSWORD,
                    'transport_zone_uuid': settings.NSX_TRANSPORT_ZONE,
                    'l3_gw_service_uuid': settings.L3_SERVICE_UUID,
                    'nsx_controllers': settings.NSX_CONTROLLER_ENDPOINT,
                    'packages_url': settings.URL_TO_NSX_BITS,
                    'connector_type': 'stt'
                }

            )
            self.fuel_web.update_nodes(
                cluster_id,
                {
                    'slave-01': ['controller'],
                    'slave-02': ['controller'],
                    'slave-03': ['controller'],
                    'slave-04': ['compute'],
                    'slave-05': ['cinder']
                }
            )

            self.fuel_web.provisioning_cluster_wait(cluster_id)
            self.fuel_web.deploy_task_wait(cluster_id=cluster_id, progress=40)
            try:
                self.fuel_web.stop_deployment_wait(cluster_id)
            except Exception:
                    logger.debug(traceback.format_exc())
            self.fuel_web.wait_nodes_get_online_state(
                self.env.nodes().slaves[:5])
            self.fuel_web.deploy_cluster_wait(cluster_id)
            self.fuel_web.verify_network(cluster_id)
            self.fuel_web.run_ostf(cluster_id=cluster_id)
            self.env.make_snapshot("deploy_nsx_HA_stt_stop_deployment")

    @test(depends_on=[SetupEnvironment.prepare_slaves_5],
          groups=["deploy_nsx_HA_stt_delete_node"])
    @log_snapshot_on_error
    def deploy_nsx_HA_stt_delete_node(self):

            """Deploy cluster in HA mode
               with Neutron NSX plugin with STT,
               with 3 controllers and 1 compute, with 1 Cinder LVM
               deploy cluster, then delete one node
               and re-deploy it again

            Scenario:
                1. Create cluster
                2. Add 3 nodes with controller roles
                3. Add 1 node with compute role
                4. Add 1 node with cinder LVM role
                5. Deploy cluster
                6. Delete one node
                7. Re-deploy cluster
                8. Run network verification
                9. Run OSTF

            Snapshot deploy_nsx_HA_stt_delete_node

            """
            self.env.revert_snapshot("ready_with_5_slaves")

            cluster_id = self.fuel_web.create_cluster(
                name=self.__class__.__name__,
                mode=settings.DEPLOYMENT_MODE_HA,
                settings={
                    'net_provider': 'neutron-nsx',
                    'volumes_lvm': True,
                    'nsx_plugin': True,
                    'nsx_username': settings.NSX_USERNAME,
                    'nsx_password': settings.NSX_PASSWORD,
                    'transport_zone_uuid': settings.NSX_TRANSPORT_ZONE,
                    'l3_gw_service_uuid': settings.L3_SERVICE_UUID,
                    'nsx_controllers': settings.NSX_CONTROLLER_ENDPOINT,
                    'packages_url': settings.URL_TO_NSX_BITS,
                    'connector_type': 'stt'
                }

            )
            self.fuel_web.update_nodes(
                cluster_id,
                {
                    'slave-01': ['controller'],
                    'slave-02': ['controller'],
                    'slave-03': ['controller'],
                    'slave-04': ['compute'],
                    'slave-05': ['cinder'],
                }

            )
            self.fuel_web.deploy_cluster_wait(cluster_id)
            self.fuel_web.client.get_cluster(cluster_id)
            self.fuel_web.update_nodes(
                cluster_id,
                {
                    'slave-03': ['controller']
                }, False, True
            )
            self.fuel_web.deploy_cluster_wait(cluster_id)
            self.fuel_web.verify_network(cluster_id)
            self.fuel_web.run_ostf(cluster_id=cluster_id)
            self.env.make_snapshot("deploy_nsx_HA_stt_delete_node")

    @test(depends_on=[SetupEnvironment.prepare_slaves_7],
          groups=["deploy_nsx_HA_stt_add_node"])
    @log_snapshot_on_error
    def deploy_nsx_HA_stt_add_node(self):

        """Deploy cluster in simple mode
           with Neutron NSX plugin with STT,
           with 3 controller and 1 compute + 1 ceph osd,
           and 1 cinder lvm and deploy cluster,
           then add one 1 node with ceph-osd role
           re-deploy cluster again

        Scenario:
            1. Create cluster
            2. Add 3 node with controller role
            3. Add 1 node with compute role +1 ceph osd
            4. Add 1 node with cinder lvm role
            5. Deploy cluster
            6. Run network verification
            7. Run OSTF
            8. Add 1 more compute role
            9. Re-deploy cluster again
            10. Run network verification

        Snapshot deploy_nsx_HA_stt_add_node

        """
        self.env.revert_snapshot("ready_with_7_slaves")

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=settings.DEPLOYMENT_MODE_HA,
            settings={
                'net_provider': 'neutron-nsx',
                'volumes_lvm': True,
                'images_ceph': True,
                'nsx_plugin': True,
                'nsx_username': settings.NSX_USERNAME,
                'nsx_password': settings.NSX_PASSWORD,
                'transport_zone_uuid': settings.NSX_TRANSPORT_ZONE,
                'l3_gw_service_uuid': settings.L3_SERVICE_UUID,
                'nsx_controllers': settings.NSX_CONTROLLER_ENDPOINT,
                'packages_url': settings.URL_TO_NSX_BITS,
                'connector_type': 'stt'
            }

        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['controller'],
                'slave-03': ['controller'],
                'slave-04': ['compute', 'ceph-osd'],
                'slave-05': ['cinder', 'ceph-osd'],
            }, True, False
        )

        self.fuel_web.deploy_cluster_wait(cluster_id)
        self.fuel_web.client.get_cluster(cluster_id)
        self.fuel_web.assert_cluster_ready(
            'slave-01', smiles_count=4, timeout=300)
        self.fuel_web.update_nodes(
            cluster_id, {
                'slave-06': ['compute']
            }, True, False
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)
        self.fuel_web.verify_network(cluster_id)
        self.fuel_web.run_ostf(cluster_id=cluster_id)
        self.env.make_snapshot("deploy_nsx_HA_stt_add_node")

    @test(depends_on=[SetupEnvironment.prepare_slaves_5],
          groups=["deploy_nsx_HA_gre_reset_node"])
    @log_snapshot_on_error
    def deploy_nsx_HA_gre_reset_node(self):

            """Deploy cluster in HA mode
               with Neutron NSX plugin with GRE,
               with 2 controllers and 1 compute,
               with 1 Cinder LVM and 1 ceph-osd,
               deploy cluster,
               then reset one node, wait some time
               then start it again
               verify ostf and network verification

            Scenario:
                1. Create cluster
                2. Add 2 nodes with controller roles
                3. Add 1 node with compute role
                4. Add 1 node with cinder LVM role
                5. Add 1 node with ceph-osd role
                6. Deploy cluster
                7. Then reset one node and wait some time
                8. Then start it again
                9. Run network verification
                10. Run OSTF

            Snapshot deploy_nsx_HA_gre_reset_node

            """
            self.env.revert_snapshot("ready_with_5_slaves")

            cluster_id = self.fuel_web.create_cluster(
                name=self.__class__.__name__,
                mode=settings.DEPLOYMENT_MODE_HA,
                settings={
                    'net_provider': 'neutron-nsx',
                    'images_ceph': True,
                    'volumes_lvm': True,
                    'nsx_plugin': True,
                    'nsx_username': settings.NSX_USERNAME,
                    'nsx_password': settings.NSX_PASSWORD,
                    'transport_zone_uuid': settings.NSX_TRANSPORT_ZONE,
                    'l3_gw_service_uuid': settings.L3_SERVICE_UUID,
                    'nsx_controllers': settings.NSX_CONTROLLER_ENDPOINT,
                    'packages_url': settings.URL_TO_NSX_BITS,
                    'connector_type': 'gre'

                }

            )
            self.fuel_web.update_nodes(
                cluster_id,
                {
                    'slave-01': ['controller'],
                    'slave-02': ['controller'],
                    'slave-03': ['compute', 'ceph-osd'],
                    'slave-04': ['cinder'],
                    'slave-05': ['ceph-osd']
                }
            )
            self.fuel_web.during_deployment_restart_node(
                cluster_id, self.env.nodes().slaves[3], progress_value=30)
            self.fuel_web.verify_network(cluster_id)
            self.fuel_web.run_ostf(cluster_id=cluster_id)
            self.env.make_snapshot("deploy_nsx_HA_gre_reset_node")
