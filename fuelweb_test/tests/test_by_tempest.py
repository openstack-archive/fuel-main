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

""" Launchers for Tempest scenarios

To launch these Fuel-tests, you should specify several properties in global
environment.

Tempest should be configured with your cluster. You can do it manually and set
path to existing configuration file in TEMPEST_CONFIG_FILE. Automatic
configuration is also presented and required cluster name
(variable: CLUSTER_NAME) and name of environment (variable: PARENT_ENV_NAME),
wherein the cluster has been created.

Another important variable is name of snapshot (variable: SNAPSHOT) which
Tempest will verify.

Optional properties:
    TEMPEST_PATH - path to Tempest (default: './tempest')
    TEMPEST_XML_LOG_FILE - path to file which will store results of
        verification in JUnit XML format
        (default: './logs/$EXEC_NUMBER_tempest.xml')

Cheat:
    TEMPEST_GOD_MODE - if you specify this variable, fuel-tests will be
        marked as failed (will raise exception) only when xml log file is
        missed(don't matter Tempest scenarios are finished successfully or
        some of them are crashed).

"""

import errno
import os
import subprocess as sp
import tempfile
from xml.etree import ElementTree

from proboscis import SkipTest
from proboscis import test

from fuelweb_test.helpers.decorators import log_snapshot_on_error
from fuelweb_test.models import nailgun_client as nc
from fuelweb_test.tests import base_test_case
from fuelweb_test.helpers import conf_tempest


def _prepare_and_run(*testr_args):
    """ Prepare and run Tempest scenarios via testr.

    Required variables in environment: CLUSTER_NAME, PARENT_ENV_NAME,
        TEMPEST_PATH, TEMPEST_CONFIG_FILE, EXECUTOR_NUMBER,
        TEMPEST_XML_LOG_FILE, TEMPEST_GOD_MODE
    """

    # Preparation
    cluster = os.environ.get("CLUSTER_NAME")
    env_name = os.environ.get("PARENT_ENV_NAME")
    tempest_path = os.environ.get("TEMPEST_PATH", "./tempest")
    tempest_conf = os.environ.get("TEMPEST_CONFIG_FILE")
    exec_number = os.environ.get("EXECUTOR_NUMBER")
    xml_logfile = os.environ.get("TEMPEST_XML_LOG_FILE",
                                 "./logs/%s_tempest.xml" % exec_number)
    god_mode = os.environ.get("TEMPEST_GOD_MODE", False)

    # Check the possibility of configuration Tempest
    if not tempest_conf and (not env_name and not cluster):
        raise ValueError(
            "Use should specify Tempest configuration file or environment and "
            "cluster names for generation configuration file.")

    # Prepare directory for log file
    try:
        os.makedirs(os.path.dirname(xml_logfile))
    except OSError as exc:
        if exc.errno == errno.EEXIST:
            if not os.path.isdir(os.path.dirname(xml_logfile)):
                raise
        else:
            raise

    if not tempest_conf:
        tempest_conf = tempfile.NamedTemporaryFile().name

        # Get nailgun node ip address
        netdump = sp.Popen(["virsh", "net-dumpxml", "%s_admin" % env_name],
                           stdout=sp.PIPE).communicate()[0]
        try:
            network = ElementTree.fromstring(netdump).find('ip')
            node_ip = "%s2" % network.attrib['address'][:-1]
        except (AttributeError, KeyError):
            raise ValueError(
                "Nailgun node ip address can not be obtained using the "
                "specified name of environment('%s')" % env_name)

        cluster_id = nc.NailgunClient(node_ip).get_cluster_id(cluster)
        if not cluster_id:
            raise ValueError(
                "Cluster id can not be obtained by using specified envname"
                "('%(env_name)s') and discovered nailgun node ip address"
                "('%(ip_address)s')." % {"env_name": env_name,
                                         "ip_address": node_ip})

        # Generate config file
        conf = conf_tempest.TempestConfigState(
            node_ip, cluster_id, tempest_conf)
        conf.configure()
        conf.copy_config()

    # Tempest needs modified environment
    tempest_env = os.environ.copy()
    tempest_env["TEMPEST_CONFIG_DIR"] = tempest_path
    tempest_env["TEMPEST_CONFIG"] = os.path.basename(tempest_conf)
    tempest_env["OS_TEST_PATH"] = os.path.join(
        tempest_path, "tempest/test_discover")

    # Run Tempest
    tempest_cmd = ["testr", "run", "--parallel", "--subunit"]
    tempest_cmd.extend(testr_args)
    to_xml_cmd = ['subunit2junitxml' '--output-to', xml_logfile]

    try:
        tempest_process = sp.Popen(tempest_cmd, cwd=tempest_path,
                                   env=tempest_env, stdout=sp.PIPE)
        sp.check_call(to_xml_cmd, stdin=tempest_process.stdout,
                      cwd=tempest_path)
    except sp.CalledProcessError:
        if god_mode and not os.path.exists(xml_logfile):
            raise RuntimeError(
                "An error occurred during the execution of Tempest. "
                "Please see log files for detailed information.")
        elif not god_mode:
            raise RuntimeError(
                "Tempest tests are finished with errors. Please see xml "
                "file with results for detailed information.")


@test(groups=["tempest"])
class TestByTempest(base_test_case.TestBasic):

    def revert_snapshot(self):
        """ Prepare snapshot specified in environment"""

        success = self.env.revert_snapshot(os.environ.get("SNAPSHOT"))

        if not success:
            raise SkipTest()

    @test(groups=["tempest_set"])
    @log_snapshot_on_error
    def tempest_set(self):
        """Prepare cluster and launch Tempest tests from TEMPEST_TEST_SET

        Scenario:
            1. Revert cluster(snapshot) which Tempest will test.
            2. Prepare Tempest
            2.1 Discover nailgun node ip and cluster id (if Tempest
                configuration file is not presented)
            2.2 Modify environment
            3. Validate cluster with set of Tempest-tests

        Specific test variable:
            TEMPEST_TEST_SET - name of Tempest tests set, which will be
                launched. Allowed names:
                 - full (used by default)
                 - smoke
                 - baremetal
                 - compute
                 - data_processing
                 - identity
                 - image
                 - network
                 - object_storage
                 - orchestration
                 - telemetry
                 - volume

        """
        self.revert_snapshot()

        # Parse Tempest set name
        tempest_set = os.environ.get("TEMPEST_TEST_SET", "")

        if tempest_set and tempest_set not in ['full', 'smoke']:
            tempest_set = "tempest.api.%s" % tempest_set
        elif tempest_set != "smoke":
            tempest_set = ""

        _prepare_and_run(tempest_set)

    @test(groups=["tempest_list"])
    @log_snapshot_on_error
    def tempest_list(self):
        """Prepare cluster and launch Tempest tests from TEMPEST_TESTS_LIST

        Scenario:
            1. Revert cluster(snapshot) which Tempest will test.
            2. Prepare Tempest
            2.1 Discover nailgun node ip and cluster id (if Tempest
                configuration file is not presented)
            2.2 Modify environment
            3. Validate cluster with list of Tempest-tests

        Specific test variable:
            TEMPEST_TESTS_LIST - path to file with names of Tempests-tests
                (structure of file: each name on a separate line)

        """
        self.revert_snapshot()

        file_with_tests = os.environ.get("TEMPEST_TESTS_LIST")
        if not os.path.exists(file_with_tests):
            raise ValueError(
                "File %s should not exist. Please, specify correct path to "
                "file, which contains list of tests." % file_with_tests)

        _prepare_and_run("list-tests", file_with_tests)
