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
import urllib
import hashlib
import os.path


from glanceclient.v1 import Client as glanceclient
from keystoneclient.v2_0 import Client as keystoneclient
from novaclient.v1_1 import Client as novaclient
from proboscis.asserts import assert_true
from fuelweb_test.helpers.checkers \
    import verify_savanna_service, verify_murano_service
from fuelweb_test.helpers.decorators import debug, log_snapshot_on_error
from fuelweb_test.tests.base_test_case import TestBasic, SetupEnvironment
from fuelweb_test.settings import *

LOGGER = logging.getLogger(__name__)
LOGWRAP = debug(LOGGER)


class Common:
    """
    :param controller_ip:
    """
    def __init__(self, controller_ip):
        self.controller_ip = controller_ip

    def _get_auth_url(self):
        LOGGER.debug('Slave-01 is {0}'.format(self.controller_ip))
        return 'http://{0}:5000/v2.0/'.format(self.controller_ip)

    @staticmethod
    def check_image(url, image, md5, path=SERVTEST_LOCAL_PATH):
        download_url = "{0}/{1}".format(url, image)
        local_path = "{0}/{1}".format(path, image)
        LOGGER.debug('Check md5 {0} of image {1}/{2}'.format(md5, path, image))
        if not os.path.isfile(local_path):
            urllib.urlretrieve(download_url, local_path)
        with open(local_path, mode='rb') as fimage:
            digits = hashlib.md5()
            while True:
                buf = fimage.read(4096)
                if not buf:
                    break
                digits.update(buf)
            md5_local = digits.hexdigest()
        if md5_local != md5:
            LOGGER.debug('MD5 is not correct, download {0} to {1}'.format(
                         download_url, local_path))
            urllib.urlretrieve(download_url, local_path)
        return True

    def goodbye_security(self):
        auth_url = self._get_auth_url()
        nova = novaclient(username=SERVTEST_USERNAME,
                          api_key=SERVTEST_PASSWORD,
                          project_id=SERVTEST_TENANT,
                          auth_url=auth_url)
        LOGGER.debug('Permit all TCP and ICMP in security group default')
        secgroup = nova.security_groups.find(name='default')
        nova.security_group_rules.create(secgroup.id,
                                         ip_protocol='tcp',
                                         from_port=1,
                                         to_port=65535)
        nova.security_group_rules.create(secgroup.id,
                                         ip_protocol='icmp',
                                         from_port=-1,
                                         to_port=-1)

    def image_import(self, properties, local_path, image, image_name):
        LOGGER.debug('Import image {0}/{1} to glance'.format(local_path, image))
        auth_url = self._get_auth_url()
        LOGGER.debug('Auth URL is {0}'.format(auth_url))
        keystone = keystoneclient(username=SERVTEST_USERNAME,
                                  password=SERVTEST_PASSWORD,
                                  tenant_name=SERVTEST_TENANT,
                                  auth_url=auth_url)
        token = keystone.auth_token
        LOGGER.debug('Token is {0}'.format(token))
        glance_endpoint = keystone.service_catalog.url_for(
            service_type='image', endpoint_type='publicURL')
        LOGGER.debug('Glance endpoind is {0}'.format(glance_endpoint))
        glance = glanceclient(endpoint=glance_endpoint, token=token)
        with open('{0}/{1}'.format(local_path, image)) as fimage:
            glance.images.create(name=image_name, is_public=True,
                                 disk_format='qcow2',
                                 container_format='bare', data=fimage,
                                 properties=properties)


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


        Snapshot: deploy_savanna_simple

        """
        if OPENSTACK_RELEASE == OPENSTACK_RELEASE_REDHAT:
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
            'slave-01', smiles_count=6, networks_count=1, timeout=500)
        verify_savanna_service(self.env.get_ssh_to_remote_by_name("slave-01"))
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
        if OPENSTACK_RELEASE == OPENSTACK_RELEASE_REDHAT:
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
        check_image = common_func.check_image(SERVTEST_SAVANNA_SERVER_URL,
                                              SERVTEST_SAVANNA_IMAGE,
                                              SERVTEST_SAVANNA_IMAGE_MD5,
                                              SERVTEST_LOCAL_PATH)
        assert_true(check_image)
        common_func.image_import(SERVTEST_SAVANNA_IMAGE_META,
                                 SERVTEST_LOCAL_PATH,
                                 SERVTEST_SAVANNA_IMAGE,
                                 SERVTEST_SAVANNA_IMAGE_NAME)

        common_func.goodbye_security()

        LOGGER.debug('Run OSTF platform tests')
        test_classes = ['fuel_health.tests.platform_tests'
                        '.test_platform_savanna.'
                        'PlatformSavannaTests.test_platform_savanna']
        self.fuel_web.run_ostf_certain(
            cluster_id=self.fuel_web.get_last_created_cluster(),
            tests_must_be_passed=test_classes, test_sets='platform_tests')


@test(groups=["thread_1", "services", "services.murano"])
class MuranoSimple(TestBasic):

    @test(depends_on=[SetupEnvironment.prepare_slaves_5],
          groups=["deploy_murano_simple"])
    @log_snapshot_on_error
    def deploy_murano_simple(self):
        """Deploy cluster in simple mode with Murano

        Scenario:
            1. Create cluster. Set install Murano option
            2. Add 1 node with controller role
            3. Add 3 nodes with compute role
            4. Add 1 node with cinder role
            4. Deploy the cluster
            5. Verify murano services

        Snapshot: deploy_murano_simple

        """
        if OPENSTACK_RELEASE == OPENSTACK_RELEASE_REDHAT:
            raise SkipTest()

        self.env.revert_snapshot("ready_with_5_slaves")

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            settings={
                'murano': True
            }
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['compute'],
                'slave-03': ['compute'],
                'slave-04': ['compute'],
                'slave-05': ['cinder']
            }
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)
        self.fuel_web.assert_cluster_ready(
            'slave-01', smiles_count=10, networks_count=1, timeout=500)
        verify_murano_service(self.env.get_ssh_to_remote_by_name("slave-01"))
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
        if OPENSTACK_RELEASE == OPENSTACK_RELEASE_REDHAT:
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
        check_image = common_func.check_image(SERVTEST_MURANO_SERVER_URL,
                                              SERVTEST_MURANO_IMAGE,
                                              SERVTEST_MURANO_IMAGE_MD5,
                                              SERVTEST_LOCAL_PATH)
        assert_true(check_image)
        common_func.image_import(SERVTEST_MURANO_IMAGE_META,
                                 SERVTEST_LOCAL_PATH,
                                 SERVTEST_MURANO_IMAGE,
                                 SERVTEST_MURANO_IMAGE_NAME)
        common_func.goodbye_security()

        LOGGER.debug('Run OSTF platform tests')

        test_class_main = ('fuel_health.tests.platform_tests'
                           '.test_murano.MuranoDeploymentSmokeTests')

        tests_name = ['test_deploy_ad', 'test_deploy_iis',
                      'test_deploy_aspnet', 'test_deploy_iis_farm',
                      'test_deploy_aspnet_farm', 'test_deploy_sql',
                      'test_deploy_sql_cluster']
        test_classes = []
        for full_test_id in tests_name:
                test_classes.append('{0}.{1}'.format(test_class_main,
                                                     tests_name))
        self.fuel_web.run_ostf_certain(
            cluster_id=self.fuel_web.get_last_created_cluster(),
            tests_must_be_passed=test_classes, test_sets='platform_tests')
