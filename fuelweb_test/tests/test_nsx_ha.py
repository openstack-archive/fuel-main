import traceback

from fuelweb_test import logger
from fuelweb_test.helpers.decorators import log_snapshot_on_error
from fuelweb_test import settings
from fuelweb_test.tests.base_test_case import SetupEnvironment
from fuelweb_test.tests.base_test_case import TestBasic

from proboscis import test


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
                'volumes_lvm': False,
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

            self.deploy_cluster_wait_progress(cluster_id, progress=60)
            self.warm_restart_nodes(self.env.nodes().slaves[3])
            self.deploy_cluster_wait_progress(cluster_id)
            self.fuel_web.verify_network(cluster_id)
            self.fuel_web.run_ostf(cluster_id=cluster_id)
            self.env.make_snapshot("deploy_nsx_HA_gre_reset_node")
