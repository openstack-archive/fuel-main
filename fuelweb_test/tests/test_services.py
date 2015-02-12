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

from __future__ import division

from devops.helpers.helpers import wait
from proboscis import asserts
from proboscis import SkipTest
from proboscis import test
from proboscis.asserts import assert_equal

from fuelweb_test.helpers import checkers
from fuelweb_test.helpers.common import Common
from fuelweb_test.helpers.decorators import log_snapshot_on_error
from fuelweb_test.helpers import os_actions
from fuelweb_test import settings
from fuelweb_test import logger as LOGGER
from fuelweb_test.tests.base_test_case import SetupEnvironment
from fuelweb_test.tests.base_test_case import TestBasic


@test(groups=["services", "services.sahara", "services_ha_one_controller"])
class SaharaHAOneController(TestBasic):
    """Sahara ha with 1 controller tests.
    Don't recommend to start tests without kvm
    Put Sahara image before start
    """
    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["deploy_sahara_ha_one_controller_gre"])
    @log_snapshot_on_error
    def deploy_sahara_ha_one_controller_gre(self):
        """Deploy cluster in ha mode with 1 controller Sahara and Neutron GRE

        Scenario:
            1. Create a Fuel cluster. Set the option for Sahara installation
            2. Add 1 node with "controller" role
            3. Add 1 node with "compute" role
            4. Deploy the Fuel cluster
            5. Verify Sahara service on controller
            6. Run all sanity and smoke tests
            7. Register Vanilla2 image for Sahara
            8. Run platform Vanilla2 test for Sahara

        Duration 65m
        Snapshot: deploy_sahara_ha_one_controller_gre
        """
        if settings.OPENSTACK_RELEASE == settings.OPENSTACK_RELEASE_REDHAT:
            raise SkipTest()

        LOGGER.debug('Check MD5 sum of Vanilla2 image')
        check_image = checkers.check_image(
            settings.SERVTEST_SAHARA_VANILLA_2_IMAGE,
            settings.SERVTEST_SAHARA_VANILLA_2_IMAGE_MD5,
            settings.SERVTEST_LOCAL_PATH)
        asserts.assert_true(check_image)

        self.env.revert_snapshot("ready_with_3_slaves")

        LOGGER.debug('Create Fuel cluster for Sahara tests')
        data = {
            'sahara': True,
            'net_provider': 'neutron',
            'net_segment_type': 'gre',
            'tenant': 'saharaSimple',
            'user': 'saharaSimple',
            'password': 'saharaSimple'
        }
        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=settings.DEPLOYMENT_MODE,
            settings=data
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['compute']
            }
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)
        os_conn = os_actions.OpenStackActions(
            self.fuel_web.get_public_vip(cluster_id),
            data['user'], data['password'], data['tenant'])
        self.fuel_web.assert_cluster_ready(
            os_conn, smiles_count=5, networks_count=2, timeout=300)

        LOGGER.debug('Verify Sahara service on controller')
        checkers.verify_service(
            self.env.get_ssh_to_remote_by_name("slave-01"),
            service_name='sahara-all')

        LOGGER.debug('Run all sanity and smoke tests')
        path_to_tests = 'fuel_health.tests.sanity.test_sanity_sahara.'
        test_names = ['VanillaTwoTemplatesTest.test_vanilla_two_templates',
                      'HDPTwoTemplatesTest.test_hdp_two_templates']
        self.fuel_web.run_ostf(
            cluster_id=self.fuel_web.get_last_created_cluster(),
            tests_must_be_passed=[path_to_tests + test_name
                                  for test_name in test_names]
        )

        LOGGER.debug('Import Vanilla2 image for Sahara')
        common_func = Common(
            self.fuel_web.get_public_vip(cluster_id),
            data['user'], data['password'], data['tenant'])
        common_func.image_import(
            settings.SERVTEST_LOCAL_PATH,
            settings.SERVTEST_SAHARA_VANILLA_2_IMAGE,
            settings.SERVTEST_SAHARA_VANILLA_2_IMAGE_NAME,
            settings.SERVTEST_SAHARA_VANILLA_2_IMAGE_META)

        path_to_tests = 'fuel_health.tests.platform_tests.test_sahara.'
        test_names = ['VanillaTwoClusterTest.test_vanilla_two_cluster']
        for test_name in test_names:
            LOGGER.debug('Run platform test {0} for Sahara'.format(test_name))
            self.fuel_web.run_single_ostf_test(
                cluster_id=cluster_id, test_sets=['platform_tests'],
                test_name=path_to_tests + test_name, timeout=60 * 200)

        self.env.make_snapshot("deploy_sahara_ha_one_controller_gre")


@test(groups=["services", "services.sahara", "services_ha"])
class SaharaHA(TestBasic):
    """Sahara HA tests.
    Don't recommend to start tests without kvm
    Put Sahara image before start
    """
    @test(depends_on=[SetupEnvironment.prepare_slaves_5],
          groups=["deploy_sahara_ha_gre"])
    @log_snapshot_on_error
    def deploy_sahara_ha_gre(self):
        """Deploy cluster in HA mode with Sahara and Neutron GRE

        Scenario:
            1. Create a Fuel cluster. Set the option for Sahara installation
            2. Add 3 node with "controller" role
            3. Add 1 node with "compute" role
            4. Deploy the Fuel cluster
            5. Verify Sahara service on all controllers
            6. Run all sanity and smoke tests
            7. Register Vanilla2 image for Sahara
            8. Run platform Vanilla2 test for Sahara

        Duration 130m
        Snapshot: deploy_sahara_ha_gre

        """
        if settings.OPENSTACK_RELEASE == settings.OPENSTACK_RELEASE_REDHAT:
            raise SkipTest()

        LOGGER.debug('Check MD5 sum of Vanilla2 image')
        check_image = checkers.check_image(
            settings.SERVTEST_SAHARA_VANILLA_2_IMAGE,
            settings.SERVTEST_SAHARA_VANILLA_2_IMAGE_MD5,
            settings.SERVTEST_LOCAL_PATH)
        asserts.assert_true(check_image)

        self.env.revert_snapshot("ready_with_5_slaves")

        LOGGER.debug('Create Fuel cluster for Sahara tests')
        data = {
            'sahara': True,
            'net_provider': 'neutron',
            'net_segment_type': 'gre',
            'tenant': 'saharaHA',
            'user': 'saharaHA',
            'password': 'saharaHA'
        }
        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=settings.DEPLOYMENT_MODE,
            settings=data
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['controller'],
                'slave-03': ['controller'],
                'slave-04': ['compute']
            }
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)
        cluster_vip = self.fuel_web.get_public_vip(cluster_id)
        os_conn = os_actions.OpenStackActions(
            cluster_vip, data['user'], data['password'], data['tenant'])
        self.fuel_web.assert_cluster_ready(
            os_conn, smiles_count=13, networks_count=2, timeout=300)

        LOGGER.debug('Verify Sahara service on all controllers')
        for slave in ["slave-01", "slave-02", "slave-03"]:
            checkers.verify_service(
                self.env.get_ssh_to_remote_by_name(slave),
                service_name='sahara-all')

        LOGGER.debug('Run all sanity and smoke tests')
        path_to_tests = 'fuel_health.tests.sanity.test_sanity_sahara.'
        test_names = ['VanillaTwoTemplatesTest.test_vanilla_two_templates',
                      'HDPTwoTemplatesTest.test_hdp_two_templates']
        self.fuel_web.run_ostf(
            cluster_id=self.fuel_web.get_last_created_cluster(),
            tests_must_be_passed=[path_to_tests + test_name
                                  for test_name in test_names]
        )

        LOGGER.debug('Import Vanilla2 image for Sahara')
        common_func = Common(cluster_vip,
                             data['user'], data['password'], data['tenant'])
        common_func.image_import(
            settings.SERVTEST_LOCAL_PATH,
            settings.SERVTEST_SAHARA_VANILLA_2_IMAGE,
            settings.SERVTEST_SAHARA_VANILLA_2_IMAGE_NAME,
            settings.SERVTEST_SAHARA_VANILLA_2_IMAGE_META)

        path_to_tests = 'fuel_health.tests.platform_tests.test_sahara.'
        test_names = ['VanillaTwoClusterTest.test_vanilla_two_cluster']
        for test_name in test_names:
            LOGGER.debug('Run platform test {0} for Sahara'.format(test_name))
            self.fuel_web.run_single_ostf_test(
                cluster_id=cluster_id, test_sets=['platform_tests'],
                test_name=path_to_tests + test_name, timeout=60 * 200)

        self.env.make_snapshot("deploy_sahara_ha_gre")


@test(groups=["services", "services.murano", "services_ha_one_controller"])
class MuranoHAOneController(TestBasic):
    """Murano HA with 1 controller tests.
    Don't recommend to start tests without kvm
    Put Murano image before start
    Murano OSTF platform tests  without Internet connection will be failed
    """
    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["deploy_murano_ha_one_controller_gre"])
    @log_snapshot_on_error
    def deploy_murano_ha_one_controller_gre(self):
        """Deploy cluster in HA mode with Murano and Neutron GRE

        Scenario:
            1. Create cluster. Set install Murano option
            2. Add 1 node with controller role
            3. Add 1 nodes with compute role
            4. Deploy the cluster
            5. Verify Murano services
            6. Run OSTF
            7. Register Murano image
            8. Run OSTF Murano platform tests

        Duration 40m
        Snapshot: deploy_murano_ha_one_controller_gre
        """
        if settings.OPENSTACK_RELEASE == settings.OPENSTACK_RELEASE_REDHAT:
            raise SkipTest()

        self.env.revert_snapshot("ready_with_3_slaves")

        LOGGER.debug('Check MD5 of image')
        check_image = checkers.check_image(
            settings.SERVTEST_MURANO_IMAGE,
            settings.SERVTEST_MURANO_IMAGE_MD5,
            settings.SERVTEST_LOCAL_PATH)
        asserts.assert_true(check_image, "Image verification failed")

        data = {
            'murano': True,
            'net_provider': 'neutron',
            'net_segment_type': 'gre',
            'tenant': 'muranoSimple',
            'user': 'muranoSimple',
            'password': 'muranoSimple'
        }

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=settings.DEPLOYMENT_MODE,
            settings=data)

        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['compute']
            }
        )

        self.fuel_web.deploy_cluster_wait(cluster_id)
        os_conn = os_actions.OpenStackActions(
            self.fuel_web.get_public_vip(cluster_id),
            data['user'], data['password'], data['tenant'])
        self.fuel_web.assert_cluster_ready(
            os_conn, smiles_count=5, networks_count=2, timeout=300)
        checkers.verify_service(
            self.env.get_ssh_to_remote_by_name("slave-01"),
            service_name='murano-api')

        common_func = Common(self.fuel_web.get_public_vip(cluster_id),
                             data['user'], data['password'],
                             data['tenant'])

        LOGGER.debug('Run sanity and functional Murano OSTF tests')
        self.fuel_web.run_single_ostf_test(
            cluster_id=self.fuel_web.get_last_created_cluster(),
            test_sets=['sanity'],
            test_name=('fuel_health.tests.sanity.test_sanity_murano.'
                       'MuranoSanityTests.test_create_and_delete_service')
        )

        LOGGER.debug('Import Murano image')
        common_func.image_import(
            settings.SERVTEST_LOCAL_PATH,
            settings.SERVTEST_MURANO_IMAGE,
            settings.SERVTEST_MURANO_IMAGE_NAME,
            settings.SERVTEST_MURANO_IMAGE_META)

        LOGGER.debug('Boot instance with Murano image')

        image_name = settings.SERVTEST_MURANO_IMAGE_NAME
        srv = common_func.create_instance(flavor_name='test_murano_flavor',
                                          ram=2048, vcpus=1, disk=20,
                                          server_name='murano_instance',
                                          image_name=image_name,
                                          neutron_network=True)

        wait(lambda: common_func.get_instance_detail(srv).status == 'ACTIVE',
             timeout=60 * 60)

        common_func.delete_instance(srv)

        LOGGER.debug('Run OSTF platform tests')

        test_class_main = ('fuel_health.tests.platform_tests'
                           '.test_murano_linux.MuranoDeployLinuxServicesTests')
        tests_names = ['test_deploy_apache_service', ]

        test_classes = []

        for test_name in tests_names:
            test_classes.append('{0}.{1}'.format(test_class_main,
                                                 test_name))

        for test_name in test_classes:
            self.fuel_web.run_single_ostf_test(
                cluster_id=cluster_id, test_sets=['platform_tests'],
                test_name=test_name, timeout=60 * 36)

        self.env.make_snapshot("deploy_murano_ha_one_controller_gre")


@test(groups=["services", "services.murano", "services_ha"])
class MuranoHA(TestBasic):
    """Murano HA tests.
    Don't recommend to start tests without kvm
    Put Murano image before start
    Murano OSTF platform tests  without Internet connection will be failed
    """
    @test(depends_on=[SetupEnvironment.prepare_slaves_5],
          groups=["deploy_murano_ha_with_gre"])
    @log_snapshot_on_error
    def deploy_murano_ha_with_gre(self):
        """Deploy cluster in ha mode with Murano and Neutron GRE

        Scenario:
            1. Create cluster. Set install Murano option
            2. Add 3 node with controller role
            3. Add 1 nodes with compute role
            4. Deploy the cluster
            5. Verify Murano services
            6. Run OSTF
            7. Register Murano image
            8. Run OSTF Murano platform tests

        Duration 100m
        Snapshot: deploy_murano_ha_with_gre

        """
        self.env.revert_snapshot("ready_with_5_slaves")

        LOGGER.debug('Check MD5 of image')
        check_image = checkers.check_image(
            settings.SERVTEST_MURANO_IMAGE,
            settings.SERVTEST_MURANO_IMAGE_MD5,
            settings.SERVTEST_LOCAL_PATH)
        asserts.assert_true(check_image, "Image verification failed")

        data = {
            'murano': True,
            'net_provider': 'neutron',
            'net_segment_type': 'gre',
            'tenant': 'muranoHA',
            'user': 'muranoHA',
            'password': 'muranoHA'
        }

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=settings.DEPLOYMENT_MODE,
            settings=data)

        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['controller'],
                'slave-03': ['controller'],
                'slave-04': ['compute']
            }
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)
        cluster_vip = self.fuel_web.get_public_vip(cluster_id)
        os_conn = os_actions.OpenStackActions(
            cluster_vip, data['user'], data['password'], data['tenant'])
        self.fuel_web.assert_cluster_ready(
            os_conn, smiles_count=13, networks_count=2, timeout=300)
        for slave in ["slave-01", "slave-02", "slave-03"]:
            checkers.verify_service(
                self.env.get_ssh_to_remote_by_name(slave),
                service_name='murano-api')

        common_func = Common(cluster_vip, data['user'], data['password'],
                             data['tenant'])

        LOGGER.debug('Run sanity and functional Murano OSTF tests')
        self.fuel_web.run_single_ostf_test(
            cluster_id=self.fuel_web.get_last_created_cluster(),
            test_sets=['sanity'],
            test_name=('fuel_health.tests.sanity.test_sanity_murano.'
                       'MuranoSanityTests.test_create_and_delete_service')
        )

        LOGGER.debug('Import Murano image')
        common_func.image_import(
            settings.SERVTEST_LOCAL_PATH,
            settings.SERVTEST_MURANO_IMAGE,
            settings.SERVTEST_MURANO_IMAGE_NAME,
            settings.SERVTEST_MURANO_IMAGE_META)

        LOGGER.debug('Boot instance with Murano image')

        image_name = settings.SERVTEST_MURANO_IMAGE_NAME
        srv = common_func.create_instance(flavor_name='test_murano_flavor',
                                          ram=2048, vcpus=1, disk=20,
                                          server_name='murano_instance',
                                          image_name=image_name,
                                          neutron_network=True)

        wait(lambda: common_func.get_instance_detail(srv).status == 'ACTIVE',
             timeout=60 * 60)

        common_func.delete_instance(srv)

        LOGGER.debug('Run OSTF platform tests')

        test_class_main = ('fuel_health.tests.platform_tests'
                           '.test_murano_linux.MuranoDeployLinuxServicesTests')
        tests_names = ['test_deploy_apache_service', ]

        test_classes = []

        for test_name in tests_names:
            test_classes.append('{0}.{1}'.format(test_class_main,
                                                 test_name))

        for test_name in test_classes:
            self.fuel_web.run_single_ostf_test(
                cluster_id=cluster_id, test_sets=['platform_tests'],
                test_name=test_name, timeout=60 * 36)

        self.env.make_snapshot("deploy_murano_ha_with_gre")


class CeilometerOSTFTestsRun(TestBasic):

    def run_tests(self, cluster_id):
        """Method run smoke, sanity and platform Ceilometer tests."""

        LOGGER.debug('Run sanity and smoke tests')
        self.fuel_web.run_ostf(
            cluster_id=cluster_id,
            test_sets=['smoke', 'sanity'],
            timeout=60 * 10
        )

        LOGGER.debug('Run platform OSTF Ceilometer tests')

        test_class_main = ('fuel_health.tests.platform_tests.'
                           'test_ceilometer.'
                           'CeilometerApiPlatformTests')
        tests_names = ['test_check_alarm_state',
                       'test_create_sample']

        test_classes = []

        for test_name in tests_names:
            test_classes.append('{0}.{1}'.format(test_class_main,
                                                 test_name))

        for test_name in test_classes:
            self.fuel_web.run_single_ostf_test(
                cluster_id=cluster_id, test_sets=['platform_tests'],
                test_name=test_name, timeout=60 * 20)


@test(groups=["services", "services.ceilometer", "services_ha_one_controller"])
class CeilometerHAOneControllerMongo(CeilometerOSTFTestsRun):

    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["deploy_ceilometer_ha_one_controller_with_mongo"])
    @log_snapshot_on_error
    def deploy_ceilometer_ha_one_controller_with_mongo(self):
        """Deploy cluster in HA mode with Ceilometer

        Scenario:
            1. Create cluster. Set install Ceilometer option
            2. Add 1 node with controller role
            3. Add 1 nodes with compute role
            4. Add 1 node with cinder role
            5. Add 1 node with mongo role
            6. Deploy the cluster
            7. Verify ceilometer api is running
            8. Run OSTF

        Duration 45m
        Snapshot: deploy_ceilometer_ha_one_controller_with_mongo
        """
        self.env.revert_snapshot("ready_with_3_slaves")

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=settings.DEPLOYMENT_MODE,
            settings={
                'ceilometer': True,
                'tenant': 'ceilometerSimple',
                'user': 'ceilometerSimple',
                'password': 'ceilometerSimple'
            }
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['compute', 'cinder'],
                'slave-03': ['mongo']
            }
        )
        nailgun_nodes = self.fuel_web.client.list_cluster_nodes(cluster_id)

        disk_mb = 0
        for node in nailgun_nodes:
            if node.get('pending_roles') == ['mongo']:
                disk_mb = self.fuel_web.get_node_disk_size(node.get('id'),
                                                           "vda")

        LOGGER.debug('disk size is {0}'.format(disk_mb))
        mongo_disk_mb = 11116
        os_disk_mb = disk_mb - mongo_disk_mb
        mongo_disk_gb = ("{0}G".format(round(mongo_disk_mb / 1024, 1)))
        disk_part = {
            "vda": {
                "os": os_disk_mb,
                "mongo": mongo_disk_mb
            }
        }

        for node in nailgun_nodes:
            if node.get('pending_roles') == ['mongo']:
                self.fuel_web.update_node_disk(node.get('id'), disk_part)

        self.fuel_web.deploy_cluster_wait(cluster_id)

        checkers.verify_service(
            self.env.get_ssh_to_remote_by_name("slave-01"),
            service_name='ceilometer-api')

        partitions = checkers.get_mongo_partitions(
            self.env.get_ssh_to_remote_by_name("slave-03"), "vda5")
        assert_equal(partitions[0].rstrip(), mongo_disk_gb,
                     'Mongo size {0} before deployment is not equal'
                     ' to size after {1}'.format(mongo_disk_gb, partitions))

        self.run_tests(cluster_id)
        self.env.make_snapshot(
            "deploy_ceilometer_ha_one_controller_with_mongo")

    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["deploy_ceilometer_ha_one_controller_multirole"])
    @log_snapshot_on_error
    def deploy_ceilometer_ha_one_controller_multirole(self):
        """Deploy cluster in ha multirole mode with Ceilometer

        Scenario:
            1. Create cluster. Set install Ceilometer option
            2. Add 1 node with controller role
            3. Add 1 nodes with compute role
            4. Add 2 nodes with cinder and mongo roles
            5. Deploy the cluster
            6. Verify ceilometer api is running
            7. Run OSTF

        Duration 35m
        Snapshot: deploy_ceilometer_ha_one_controller_multirole
        """
        self.env.revert_snapshot("ready_with_3_slaves")

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=settings.DEPLOYMENT_MODE,
            settings={
                'ceilometer': True
            }
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['compute'],
                'slave-03': ['cinder', 'mongo']
            }
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)

        checkers.verify_service(
            self.env.get_ssh_to_remote_by_name("slave-01"),
            service_name='ceilometer-api')

        self.run_tests(cluster_id)
        self.env.make_snapshot("deploy_ceilometer_ha_one_controller_mulirole")


@test(groups=["services", "services.ceilometer", "services_ha"])
class CeilometerHAMongo(CeilometerOSTFTestsRun):
    @test(depends_on=[SetupEnvironment.prepare_slaves_5],
          groups=["deploy_ceilometer_ha_with_mongo"])
    @log_snapshot_on_error
    def deploy_ceilometer_ha_with_mongo(self):
        """Deploy cluster in ha mode with Ceilometer

        Scenario:
            1. Create cluster. Set install Ceilometer option
            2. Add 3 node with controller role
            3. Add 1 nodes with compute role
            4. Add 1 node with mongo role
            5. Deploy the cluster
            6. Verify ceilometer api is running
            7. Run OSTF

        Duration 65m
        Snapshot: deploy_ceilometer_ha_with_mongo

        """

        self.env.revert_snapshot("ready_with_5_slaves")

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=settings.DEPLOYMENT_MODE,
            settings={
                'ceilometer': True,
                'tenant': 'ceilometerHA',
                'user': 'ceilometerHA',
                'password': 'ceilometerHA'
            }
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['controller'],
                'slave-03': ['controller'],
                'slave-04': ['compute'],
                'slave-05': ['mongo']
            }
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)

        checkers.verify_service(
            self.env.get_ssh_to_remote_by_name("slave-01"),
            service_name='ceilometer-api')

        self.run_tests(cluster_id)
        self.env.make_snapshot("deploy_ceilometer_ha_with_mongo")

    @test(depends_on=[SetupEnvironment.prepare_slaves_5],
          groups=["deploy_ceilometer_ha_multirole"])
    @log_snapshot_on_error
    def deploy_ceilometer_ha_multirole(self):
        """Deploy cluster in ha multirole mode with Ceilometer

        Scenario:
            1. Create cluster. Set install Ceilometer option
            2. Add 3 node with controller and mongo roles
            3. Add 1 nodes with compute role
            4. Add 1 nodes with cinder
            5. Deploy the cluster
            6. Verify ceilometer api is running
            7. Run OSTF

        Duration 80m
        Snapshot: deploy_ceilometer_ha_multirole

        """
        self.env.revert_snapshot("ready_with_5_slaves")

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=settings.DEPLOYMENT_MODE,
            settings={
                'ceilometer': True
            }
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller', 'mongo'],
                'slave-02': ['controller', 'mongo'],
                'slave-03': ['controller', 'mongo'],
                'slave-04': ['compute'],
                'slave-05': ['cinder']
            }
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)

        checkers.verify_service(
            self.env.get_ssh_to_remote_by_name("slave-01"),
            service_name='ceilometer-api')

        self.run_tests(cluster_id)
        self.env.make_snapshot("deploy_ceilometer_ha_mulirole")


@test(groups=["services", "services.heat", "services_ha_one_controller"])
class HeatHAOneController(TestBasic):
    """Heat HA one controller test.
    Don't recommend to start tests without kvm
    """
    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["deploy_heat_ha_one_controller_neutron"])
    @log_snapshot_on_error
    def deploy_heat_ha_one_controller_neutron(self):
        """Deploy Heat cluster in HA mode with Neutron GRE

        Scenario:
            1. Create cluster
            2. Add 1 node with controller role and mongo
            3. Add 1 nodes with compute role
            4. Set install Ceilometer option
            5. Deploy the cluster
            6. Verify Heat, Ceilometer services
            7. Run OSTF platform tests

        Duration 40m
        Snapshot: deploy_heat_ha_one_controller_neutron
        """

        self.env.revert_snapshot("ready_with_3_slaves")

        data = {
            'ceilometer': True,
            'net_provider': 'neutron',
            'net_segment_type': 'gre',
            'tenant': 'heatSimple',
            'user': 'heatSimple',
            'password': 'heatSimple'
        }

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=settings.DEPLOYMENT_MODE,
            settings=data)

        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller', 'mongo'],
                'slave-02': ['compute']
            }
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)

        os_conn = os_actions.OpenStackActions(
            self.fuel_web.get_public_vip(cluster_id),
            data['user'], data['password'], data['tenant'])
        self.fuel_web.assert_cluster_ready(
            os_conn, smiles_count=5, networks_count=2, timeout=300)

        checkers.verify_service(
            self.env.get_ssh_to_remote_by_name("slave-01"),
            service_name='heat-api', count=3)

        checkers.verify_service(
            self.env.get_ssh_to_remote_by_name("slave-01"),
            service_name='ceilometer-api')

        LOGGER.debug('Run Heat OSTF platform tests')

        test_class_main = ('fuel_health.tests.platform_tests.'
                           'test_heat.'
                           'HeatSmokeTests')
        tests_names = ['test_actions',
                       'test_autoscaling',
                       'test_rollback',
                       'test_update']

        test_classes = []

        for test_name in tests_names:
            test_classes.append('{0}.{1}'.format(test_class_main,
                                                 test_name))

        for test_name in test_classes:
            self.fuel_web.run_single_ostf_test(
                cluster_id=cluster_id, test_sets=['platform_tests'],
                test_name=test_name, timeout=60 * 60)

        self.env.make_snapshot("deploy_heat_ha_one_controller_neutron")

    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["deploy_heat_ha_one_controller_nova"])
    @log_snapshot_on_error
    def deploy_heat_ha_one_controller_nova(self):
        """Deploy Heat cluster in ha mode with Nova Network

        Scenario:
            1. Create cluster
            2. Add 1 node with controller role and mongo
            3. Add 1 nodes with compute role
            4. Set Ceilometer install option
            4. Deploy the cluster
            5. Verify Heat, Ceilometer services
            6. Run OSTF platform tests

        Duration 40m
        Snapshot: deploy_heat_ha_one_controller_nova
        """

        self.env.revert_snapshot("ready_with_3_slaves")

        data = {
            'ceilometer': True,
            'tenant': 'heatSimple',
            'user': 'heatSimple',
            'password': 'heatSimple'
        }

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=settings.DEPLOYMENT_MODE,
            settings=data)

        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller', 'mongo'],
                'slave-02': ['compute']
            }
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)

        os_conn = os_actions.OpenStackActions(
            self.fuel_web.get_public_vip(cluster_id),
            data['user'], data['password'], data['tenant'])
        self.fuel_web.assert_cluster_ready(
            os_conn, smiles_count=6, networks_count=1, timeout=300)

        checkers.verify_service(
            self.env.get_ssh_to_remote_by_name("slave-01"),
            service_name='heat-api', count=3)

        checkers.verify_service(
            self.env.get_ssh_to_remote_by_name("slave-01"),
            service_name='ceilometer-api')

        LOGGER.debug('Run Heat OSTF platform tests')

        test_class_main = ('fuel_health.tests.platform_tests.'
                           'test_heat.'
                           'HeatSmokeTests')
        tests_names = ['test_actions',
                       'test_autoscaling',
                       'test_rollback',
                       'test_update']

        test_classes = []

        for test_name in tests_names:
            test_classes.append('{0}.{1}'.format(test_class_main,
                                                 test_name))

        for test_name in test_classes:
            self.fuel_web.run_single_ostf_test(
                cluster_id=cluster_id, test_sets=['platform_tests'],
                test_name=test_name, timeout=60 * 60)

        self.env.make_snapshot("deploy_heat_ha_one_controller_nova")


@test(groups=["services", "services.heat", "services_ha"])
class HeatHA(TestBasic):
    """Heat HA test.
    Don't recommend to start tests without kvm
    """
    @test(depends_on=[SetupEnvironment.prepare_slaves_5],
          groups=["deploy_heat_ha"])
    @log_snapshot_on_error
    def deploy_heat_ha(self):
        """Deploy Heat cluster in HA mode

        Scenario:
            1. Create cluster
            2. Add 3 node with controller role and mongo
            3. Add 1 nodes with compute role
            4. Set Ceilometer install option
            4. Deploy the cluster
            5. Verify Heat and Ceilometer services
            6. Run OSTF platform tests

        Duration 70m
        Snapshot: deploy_heat_ha

        """

        self.env.revert_snapshot("ready_with_5_slaves")

        data = {
            'ceilometer': True,
            'net_provider': 'neutron',
            'net_segment_type': 'gre',
            'tenant': 'heatHA',
            'user': 'heatHA',
            'password': 'heatHA'
        }

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=settings.DEPLOYMENT_MODE,
            settings=data)

        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller', 'mongo'],
                'slave-02': ['controller', 'mongo'],
                'slave-03': ['controller', 'mongo'],
                'slave-04': ['compute']
            }
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)

        cluster_vip = self.fuel_web.get_public_vip(cluster_id)
        os_conn = os_actions.OpenStackActions(
            cluster_vip, data['user'], data['password'], data['tenant'])
        self.fuel_web.assert_cluster_ready(
            os_conn, smiles_count=13, networks_count=2, timeout=300)

        for slave in ["slave-01", "slave-02", "slave-03"]:
            checkers.verify_service(
                self.env.get_ssh_to_remote_by_name(slave),
                service_name='heat-api', count=3)

            checkers.verify_service(
                self.env.get_ssh_to_remote_by_name(slave),
                service_name='ceilometer-api')

        LOGGER.debug('Run Heat OSTF platform tests')

        test_class_main = ('fuel_health.tests.platform_tests.'
                           'test_heat.'
                           'HeatSmokeTests')
        tests_names = ['test_actions',
                       'test_rollback']

        test_classes = []

        for test_name in tests_names:
            test_classes.append('{0}.{1}'.format(test_class_main,
                                                 test_name))

        for test_name in test_classes:
            self.fuel_web.run_single_ostf_test(
                cluster_id=cluster_id, test_sets=['platform_tests'],
                test_name=test_name, timeout=60 * 60)

        self.env.make_snapshot("deploy_heat_ha")
