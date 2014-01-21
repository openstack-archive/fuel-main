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

import logging
import os
import subprocess


from proboscis import test
from proboscis.asserts import assert_equal
from savanna import tests as savanna_integration_tests
from fuelweb_test.helpers import services_prepare
from fuelweb_test.helpers.decorators import debug, log_snapshot_on_error
from fuelweb_test.tests import base_test_case

LOGGER = logging.getLogger(__name__)
LOGWRAP = debug(LOGGER)


@test(groups=["services_extended", "services_extended.savanna"])
class SavannaIntegration(base_test_case.TestBasic):
    """
    Run Savanna integration tests
    """
    @test(depends_on=[base_test_case.SetupEnvironment.prepare_slaves_3],
          groups=["deploy_savanna_integration"])
    @log_snapshot_on_error
    def deploy_savanna_simple(self):
        """Deploy cluster in simple mode with Savanna

        Scenario:
            1. Create cluster. Set install Savanna option
            2. Add 1 node with controller role
            3. Add 1 node with compute role
            4. Deploy the cluster
            5. Run savanna integration tests

        Snapshot: deploy_savanna_integration

        """
        services_prepare.savanna_check_image(hdp=True)

        self.env.revert_snapshot("ready_with_3_slaves")

        services_prepare.services_prepare_lab(
            self.fuel_web, self.env, self.__class__.__name__,
            {'savanna': True}, ['savanna-api'], 6)

        hdp_image_id, vanilla_image_id = \
            services_prepare.savanna_prepare_env(self.fuel_web, hdp=True)

        tests_path = os.path.dirname(savanna_integration_tests.__file__)

        services_prepare.savanna_prepare_integration_tests(
            tests_path, self.fuel_web, hdp_image_id, vanilla_image_id)

        LOGGER.debug('Start integration tests in {0}'.format(tests_path))
        os.chdir(tests_path)
        integration_tests_code_return = subprocess.call(
            ['nosetests', '-v', '{0}/integration'.format(tests_path)],
            stderr=subprocess.STDOUT)
        assert_equal(integration_tests_code_return, 0)
