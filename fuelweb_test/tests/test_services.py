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

from fuelweb_test.helpers.ci import assert_savanna_service, assert_murano_service
from fuelweb_test.helpers.decorators import debug, log_snapshot_on_error
from fuelweb_test.tests.base_test_case import TestBasic

logger = logging.getLogger(__name__)
logwrap = debug(logger)


@test
class SavannaSimple(TestBasic):
    @log_snapshot_on_error
    @test(groups=["thread_1"], depends_on=[TestBasic.prepare_5_slaves])
    def deploy_savanna_simple(self):
        self.env.revert_snapshot("ready_with_5_slaves")

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
                'slave-02': ['compute'],
                'slave-03': ['compute'],
                'slave-04': ['compute'],
                'slave-05': ['cinder']
            }
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)
        self.fuel_web.assert_cluster_ready(
            'slave-01', smiles_count=10, networks_count=1, timeout=500)
        assert_savanna_service(self.env.get_ssh_to_remote_by_name("slave-01"))
        self.env.make_snapshot("deploy_savanna_simple")

    @log_snapshot_on_error
    @test(groups=["thread_1"], depends_on=[deploy_savanna_simple])
    def simple_flat_ostf(self):
        self.env.revert_snapshot("deploy_savanna_simple")

        self.fuel_web.run_ostf(
            cluster_id=self.fuel_web.get_last_created_cluster(),
            should_fail=5, should_pass=19
        )


@test
class MuranoSimple(TestBasic):
    @log_snapshot_on_error
    @test(groups=["thread_1"], depends_on=[TestBasic.prepare_5_slaves])
    def deploy_murano_simple(self):
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
        assert_murano_service(self.env.get_ssh_to_remote_by_name("slave-01"))
        self.env.make_snapshot("deploy_murano_simple")

    @log_snapshot_on_error
    @test(groups=["thread_1"], depends_on=[deploy_murano_simple])
    def simple_flat_ostf(self):
        self.env.revert_snapshot("deploy_murano_simple")

        self.fuel_web.run_ostf(
            cluster_id=self.fuel_web.get_last_created_cluster(),
            should_fail=5, should_pass=19
        )
