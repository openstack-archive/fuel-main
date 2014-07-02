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

import os
import subprocess as sp

from proboscis import test

from fuelweb_test.helpers.decorators import log_snapshot_on_error
from fuelweb_test.models import nailgun_client as nc
from fuelweb_test.tests import base_test_case
from fuelweb_test.helpers import conf_tempest


@test(groups=["tempest"])
class TestByTempest(base_test_case.TestBasic):

    @test(depends_on=[base_test_case.SetupEnvironment.prepare_slaves_5],
          groups=["run_tempest"])
    @log_snapshot_on_error
    def run_tempest(self):
        """ Prepare cluster and launch Tempest

        Scenario:
            1. Get all variables from environment
            2. Revert cluster(snapshot) which Tempest will test.
            3. Discover nailgun node ip and cluster id(if Tempest configuration
               file is not presented)
            4. Prepare Tempest
            5. Validate cluster with Tempest

        To launch this test, you should specify several properties in global
        environment.
        First of all, you should specify name of snapshot which Tempest will
        test. Name of variable - SNAPSHOT

        Before Tempest start verification, configuration file for it should be
        created. It can be done by several ways:
            1. set path to existing configuration file in
               TEMPEST_CONFIG_FILE
            2. specify cluster name in CLUSTER_NAME and environment name in
               PARENT_ENV_NAME, which required for generation new config file

        Optional properties:
            TEMPEST_PATH - path to Tempest(default: './tempest')
            TEMPEST_TEST_SET - name of Tempest tests set, which will be
                launched (default: full set)
            TEMPEST_XML_LOG_FILE - path to file which will store results of
                verification in JUnit XML format
                (default: './logs/$EXEC_NUMBER_tempest.xml')

        """

        # Get all needed variables from global environment
        snapshot = os.environ.get("SNAPSHOT")
        cluster = os.environ.get("CLUSTER_NAME")
        env_name = os.environ.get("PARENT_ENV_NAME")
        tempest_path = os.environ.get("TEMPEST_PATH", "./tempest")
        tempest_conf = os.environ.get("TEMPEST_CONFIG_FILE")
        tempest_set = os.environ.get("TEMPEST_TEST_SET", "")
        exec_number = os.environ.get("EXECUTOR_NUMBER")
        xml_logfile = os.environ.get("TEMPEST_XML_LOG_FILE",
                                     "./logs/%s_tempest.xml" % exec_number)

        if tempest_set == "smoke":
            tempest_set = "smoke"
        elif tempest_set and tempest_set != "full":
            tempest_set = "tempest.api.%s" % tempest_set
        else:
            tempest_set = ""

        if not os.path.exists(os.path.dirname(xml_logfile)):
            os.makedirs(os.path.dirname(xml_logfile))

        if not tempest_conf and (not env_name and not cluster):
            raise AttributeError(
                "Use should specify Tempest configuration file or environment "
                "and cluster names for generation configuration file.")

        # Prepare given snapshot
        self.env.revert_snapshot(snapshot)

        if not tempest_conf:
            # Get nailgun node ip address
            net_dump_cmd = ["virsh", "net-dumpxml", "%s_admin" % env_name]
            parsing_cmd = ("grep --perl-regexp '(\d+\.){3}' -o | head -1 | "
                           "awk '{print $0\"2\"}'")
            net_dump_proc = sp.Popen(net_dump_cmd, stdout=sp.PIPE)
            parsing_proc = sp.Popen(parsing_cmd, stdin=net_dump_proc.stdout,
                                    stdout=sp.PIPE)
            net_dump_proc.stdout.close()
            node_ip = parsing_proc.communicate()[0]
            if not node_ip:
                raise ValueError(
                    "Nailgun node ip address can not be obtained using the "
                    "specified name of environment('%s')" % env_name)

            # Get cluster id
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

        # Modify environment for Tempest
        tempest_env = os.environ.copy()
        tempest_env["TEMPEST_CONFIG_DIR"] = tempest_path
        tempest_env["TEMPEST_CONFIG"] = os.path.basename(tempest_conf)
        tempest_env["OS_TEST_PATH"] = os.path.join(
            tempest_path, "tempest/test_discover")

        # Run Tempest
        tempest_cmd = ["testr", "run", "--parallel", "--subunit", tempest_set]
        to_xml_cmd = ['subunit2junitxml' '--output-to', xml_logfile]

        try:
            tempest_process = sp.Popen(tempest_cmd, cwd=tempest_path,
                                       env=tempest_env, stdout=sp.PIPE)
            sp.check_call(
                to_xml_cmd, stdin=tempest_process.stdout, cwd=tempest_path)
        except sp.CalledProcessError:
            raise RuntimeError(
                "Tempest tests are finished with errors. Please see log file "
                "'%s' for detailed information." % xml_logfile)
