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

import ConfigParser
import logging
import os
import subprocess


from proboscis.asserts import assert_true
from fuelweb_test.helpers import checkers
from fuelweb_test.helpers.common import Common
from fuelweb_test.helpers.decorators import debug
from fuelweb_test import settings


LOGGER = logging.getLogger(__name__)
LOGWRAP = debug(LOGGER)


def savanna_check_image(hdp=False):
        if hdp:
            LOGGER.debug('Check MD5 of savanna hdp image')
            check_hdp_image = (
                settings.SERVTEST_SAVANNA_HDP_SERVER_URL,
                settings.SERVTEST_SAVANNA_HDP_IMAGE,
                settings.SERVTEST_SAVANNA_HDP_IMAGE_MD5,
                settings.SERVTEST_LOCAL_PATH)
            assert_true(check_hdp_image)
        LOGGER.debug('Check MD5 of savanna image')
        check_image = checkers.check_image(
            settings.SERVTEST_SAVANNA_SERVER_URL,
            settings.SERVTEST_SAVANNA_IMAGE,
            settings.SERVTEST_SAVANNA_IMAGE_MD5,
            settings.SERVTEST_LOCAL_PATH)
        assert_true(check_image)


def savanna_prepare_env(fuel_web, hdp=False):
    controller_ip = fuel_web.get_nailgun_node_by_name(
        'slave-01')['ip']
    common_func = Common(controller_ip,
                         settings.SERVTEST_USERNAME,
                         settings.SERVTEST_PASSWORD,
                         settings.SERVTEST_TENANT)
    hdp_image_id = None
    if hdp:
        LOGGER.debug('Import hdp image')
        hdp_image_id = common_func.image_import(
            settings.SERVTEST_SAVANNA_HDP_IMAGE_META,
            settings.SERVTEST_LOCAL_PATH,
            settings.SERVTEST_SAVANNA_HDP_IMAGE,
            settings.SERVTEST_SAVANNA_HDP_IMAGE_NAME)

    LOGGER.debug('Import savanna image')
    vanilla_image_id = common_func.image_import(
        settings.SERVTEST_SAVANNA_IMAGE_META,
        settings.SERVTEST_LOCAL_PATH,
        settings.SERVTEST_SAVANNA_IMAGE,
        settings.SERVTEST_SAVANNA_IMAGE_NAME)

    common_func.goodbye_security()
    key_private = common_func.create_key('savanna')
    fp = os.open(settings.SERVTEST_KEY_FILE,
                 os.O_WRONLY | os.O_CREAT, 0o600)
    with os.fdopen(fp, 'w') as f:
        f.write(key_private)

    return hdp_image_id, vanilla_image_id


def savanna_prepare_integration_tests(tests_path, fuel_web,
                                      hdp_image_id, vanilla_image_id):
    controller_ip = fuel_web.get_nailgun_node_by_name(
        'slave-01')['ip']
    config_file = '{0}/integration/configs/itest.conf'.format(tests_path)
    config = ConfigParser.RawConfigParser()
    config.optionxform = str
    auth_url = 'http://{0}:5000/v2.0/'.format(controller_ip)

    config.add_section('COMMON')
    config.set('COMMON', 'OS_USERNAME', settings.SERVTEST_USERNAME)
    config.set('COMMON', 'OS_PASSWORD', settings.SERVTEST_PASSWORD)
    config.set('COMMON', 'OS_TENANT_NAME', settings.SERVTEST_TENANT)
    config.set('COMMON', 'OS_AUTH_URL', auth_url)
    config.set('COMMON', 'SAVANNA_HOST', controller_ip)
    config.set('COMMON', 'USER_KEYPAIR_ID',
               settings.SERVTEST_SAVANNA_IMAGE_NAME)
    config.set('COMMON', 'PATH_TO_SSH_KEY',
               settings.SERVTEST_KEY_FILE)
    config.add_section('VANILLA')
    config.set('VANILLA', 'IMAGE_ID', vanilla_image_id)
    config.add_section('HDP')
    config.set('HDP', 'IMAGE_ID', hdp_image_id)

    tmp_config_file = '{0}/itest.conf'.format(settings.SERVTEST_LOCAL_PATH)

    with open(tmp_config_file, 'wb') as configfile:
        config.write(configfile)
    command_output = subprocess.call(['sudo', 'mv', '-f',
                                      tmp_config_file, config_file],
                                      stderr=subprocess.STDOUT)
    LOGGER.debug(command_output)


def services_prepare_lab(fuel_web,
                         env,
                         name,
                         cluster_settings,
                         services,
                         smiles_count,
                         cluster_nodes=None):

        cluster_nodes = cluster_nodes or {
            'slave-01': ['controller'],
            'slave-02': ['compute']
        }

        LOGGER.debug('Create cluster for tests')
        cluster_id = fuel_web.create_cluster(
            name=name,
            settings=cluster_settings
        )
        fuel_web.update_nodes(
            cluster_id,
            cluster_nodes
        )
        fuel_web.deploy_cluster_wait(cluster_id)

        fuel_web.assert_cluster_ready(
            'slave-01', smiles_count=smiles_count, networks_count=1, timeout=300)

        for service in services:
            checkers.verify_service(
                env.get_ssh_to_remote_by_name("slave-01"),
                service_name=service)
