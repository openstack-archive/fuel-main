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
from proboscis import test, SkipTest

from proboscis.asserts import assert_true
from fuelweb_test.helpers import checkers
from fuelweb_test.helpers.common import Common
from fuelweb_test.helpers.decorators import debug, log_snapshot_on_error
from fuelweb_test.tests.base_test_case import TestBasic, SetupEnvironment
from fuelweb_test import settings

LOGGER = logging.getLogger(__name__)
LOGWRAP = debug(LOGGER)


@test(groups=["thread_1", "services", "services.savanna"])
class SavannaSimple(TestBasic):
    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["deploy_savanna_simple"])
    @log_snapshot_on_error
    def deploy_savanna_simple(self):
        """Deploy cluster in simple mode with Savanna

        Scenario:
            1. Create cluster. Set install Savanna option
            2. Add 1 node with controller role
            3. Add 1 node with compute role
            4. Deploy the cluster
            5. Verify savanna services
            6. Run OSTF


        Snapshot: deploy_savanna_simple

        """
        if settings.OPENSTACK_RELEASE == settings.OPENSTACK_RELEASE_REDHAT:
            raise SkipTest()

        self.env.revert_snapshot("ready_with_3_slaves")

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            settings={
                'savanna': True
            }
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
        checkers.verify_service(
            self.env.get_ssh_to_remote_by_name("slave-01"),
            service_name='savanna-api')
        self.env.make_snapshot("deploy_savanna_simple")

    @test(depends_on=[deploy_savanna_simple],
          groups=["deploy_savanna_simple_ostf"])
    @log_snapshot_on_error
    def deploy_savanna_simple_ostf(self):
        """Run OSTF tests on cluster in simple mode with Savanna

        Scenario:
            1. Revert snapshot "deploy_savanna_simple"
            2. Run OSTF
            3. Register savanna image
            4. Run OSTF platform tests

        """
        if settings.OPENSTACK_RELEASE == settings.OPENSTACK_RELEASE_REDHAT:
            raise SkipTest()
        self.env.revert_snapshot("deploy_savanna_simple")

        test_classes = ['fuel_health.tests.sanity.test_sanity_savanna.'
                        'SanitySavannaTests.test_sanity_savanna']
        self.fuel_web.run_ostf_certain(
            cluster_id=self.fuel_web.get_last_created_cluster(),
            tests_must_be_passed=test_classes
        )

        controller_ip = self.fuel_web.get_nailgun_node_by_name(
            'slave-01')['ip']
        common_func = Common(controller_ip)
        check_image = common_func.check_image(
            settings.SERVTEST_SAVANNA_SERVER_URL,
            settings.SERVTEST_SAVANNA_IMAGE,
            settings.SERVTEST_SAVANNA_IMAGE_MD5,
            settings.SERVTEST_LOCAL_PATH)
        assert_true(check_image)
        common_func.image_import(
            settings.SERVTEST_SAVANNA_IMAGE_META,
            settings.SERVTEST_LOCAL_PATH,
            settings.SERVTEST_SAVANNA_IMAGE,
            settings.SERVTEST_SAVANNA_IMAGE_NAME)

        common_func.goodbye_security()

        LOGGER.debug('Run OSTF platform tests')
        test_classes = ['fuel_health.tests.platform_tests'
                        '.test_platform_savanna.'
                        'PlatformSavannaTests.test_platform_savanna']
        self.fuel_web.run_ostf_certain(
            cluster_id=self.fuel_web.get_last_created_cluster(),
            tests_must_be_passed=test_classes, test_sets='platform_tests')
        self.env.make_snapshot("deploy_savanna_simple")


@test(groups=["thread_1", "services", "services.murano"])
class MuranoSimple(TestBasic):

    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["deploy_murano_simple"])
    @log_snapshot_on_error
    def deploy_murano_simple(self):
        """Deploy cluster in simple mode with Murano

        Scenario:
            1. Create cluster. Set install Murano option
            2. Add 1 node with controller role
            3. Add 1 nodes with compute role
            4. Add 1 node with cinder role
            4. Deploy the cluster
            5. Verify murano services
            6. Run OSTF

        Snapshot: deploy_murano_simple

        """
        if settings.OPENSTACK_RELEASE == settings.OPENSTACK_RELEASE_REDHAT:
            raise SkipTest()

        self.env.revert_snapshot("ready_with_3_slaves")

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            settings={
                'murano': True,
                "net_provider": 'neutron',
                "net_segment_type": 'gre'
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
        self.fuel_web.assert_cluster_ready(
            'slave-01', smiles_count=5, networks_count=1, timeout=300)
        checkers.verify_service(
            self.env.get_ssh_to_remote_by_name("slave-01"),
            service_name='murano-api')
        checkers.verify_service(
            self.env.get_ssh_to_remote_by_name("slave-01"),
            service_name='muranoconductor')
        self.env.make_snapshot("deploy_murano_simple")

    @test(depends_on=[deploy_murano_simple],
          groups=["deploy_murano_simple_ostf"])
    @log_snapshot_on_error
    def deploy_murano_simple_ostf(self):
        """Run OSTF tests on cluster in simple mode with Murano

        Scenario:
            1. Revert snapshot "deploy_murano_simple"
            2. Run OSTF
            3. Register murano image
            4. Run OSTF platform tests

        """
        if settings.OPENSTACK_RELEASE == settings.OPENSTACK_RELEASE_REDHAT:
            raise SkipTest()

        self.env.revert_snapshot("deploy_murano_simple")

        test_classes = ['fuel_health.tests.sanity.test_sanity_murano.'
                        'MuranoSanityTests.test_create_and_delete_service']
        self.fuel_web.run_ostf_certain(
            cluster_id=self.fuel_web.get_last_created_cluster(),
            tests_must_be_passed=test_classes
        )
        controller_ip = self.fuel_web.get_nailgun_node_by_name(
            'slave-01')['ip']
        common_func = Common(controller_ip)
        check_image = common_func.check_image(
            settings.SERVTEST_MURANO_SERVER_URL,
            settings.SERVTEST_MURANO_IMAGE,
            settings.SERVTEST_MURANO_IMAGE_MD5,
            settings.SERVTEST_LOCAL_PATH)
        assert_true(check_image)
        common_func.image_import(
            settings.SERVTEST_MURANO_IMAGE_META,
            settings.SERVTEST_LOCAL_PATH,
            settings.SERVTEST_MURANO_IMAGE,
            settings.SERVTEST_MURANO_IMAGE_NAME)
        common_func.goodbye_security()

        LOGGER.debug('Run OSTF platform tests')

        test_class_main = ('fuel_health.tests.platform_tests'
                           '.test_murano.MuranoDeploymentSmokeTests')

        tests_names = ['test_deploy_ad', 'test_deploy_iis',
                       'test_deploy_aspnet', 'test_deploy_iis_farm',
                       'test_deploy_aspnet_farm', 'test_deploy_sql',
                       'test_deploy_sql_cluster']
        test_classes = []
        for test_name in tests_names:
            test_classes.append('{0}.{1}'.format(test_class_main,
                                                 test_name))
        self.fuel_web.run_ostf_certain(
            cluster_id=self.fuel_web.get_last_created_cluster(),
            tests_must_be_passed=test_classes, test_sets='platform_tests')
        self.env.make_snapshot("deploy_murano_simple")


@test(groups=["thread_1", "services", "services.ceilometer"])
class CeilometerSimple(TestBasic):

    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["deploy_ceilometer_simple"])
    @log_snapshot_on_error
    def deploy_ceilometer_simple(self):
        """Deploy cluster in simple mode with Ceilometer

        Scenario:
            1. Create cluster. Set install Ceilometer option
            2. Add 1 node with controller role
            3. Add 1 nodes with compute role
            4. Add 1 node with cinder role
            4. Deploy the cluster
            5. Verify ceilometer api is running
            6. Run ostf

        Snapshot: deploy_ceilometer_simple

        """
        if settings.OPENSTACK_RELEASE == settings.OPENSTACK_RELEASE_REDHAT:
            raise SkipTest()

        self.env.revert_snapshot("ready_with_3_slaves")

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            settings={
                'ceilometer': True
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
        self.fuel_web.assert_cluster_ready(
            'slave-01', smiles_count=6, networks_count=1, timeout=300)
        checkers.verify_service(
            self.env.get_ssh_to_remote_by_name("slave-01"),
            service_name='ceilometer-api')

        self.fuel_web.run_ostf(
            cluster_id=cluster_id,
            should_fail=4)

        self.env.make_snapshot("deploy_ceilometer_simple")
