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

import time

from proboscis.asserts import assert_true
from proboscis import test
from devops.helpers.helpers import wait
from fuelweb_test import settings
from fuelweb_test.helpers import os_actions
from fuelweb_test.helpers.decorators import log_snapshot_on_error
from fuelweb_test.tests.base_test_case import SetupEnvironment
from fuelweb_test.tests.base_test_case import TestBasic
from fuelweb_test import logger


@test(groups=["vcenter60"])
class VcenterDeploy(TestBasic):
    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["vcenter60_case_1", "vcenter60_simples"])
    @log_snapshot_on_error
    def test_case_1(self):
        """Deploy cluster with controller node only

        Scenario:
            1. Create cluster
            2. Add 1 node with controller role
            3. Deploy the cluster
            4. Validate cluster was set up correctly, there are no dead
            5. Create instance and delete instance.

        """
        self.env.revert_snapshot("ready_with_3_slaves")

        # Configure cluster
        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=settings.DEPLOYMENT_MODE_SIMPLE,
            settings={
                'volumes_lvm': False,
                'volumes_vmdk': True,
                'use_vcenter': True,
                'host_ip': settings.VCENTER_IP,
                'vc_user': settings.VCENTER_USERNAME,
                'vc_password': settings.VCENTER_PASSWORD,
                'cluster': settings.VCENTER_CLUSTERS
            }
        )
        logger.info("cluster is {}".format(cluster_id))

        # Add nodes to roles
        self.fuel_web.update_nodes(
            cluster_id,
            {'slave-01': ['controller']}
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)

        self.fuel_web.run_ostf(
            cluster_id=cluster_id, test_sets=['smoke', 'sanity'])

        self.fuel_web.update_nodes(
            cluster_id,
            {'slave-02': ['cinder']}
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)
        self.fuel_web.verify_network(cluster_id)

        self.fuel_web.run_ostf(
            cluster_id=cluster_id, test_sets=['smoke', 'sanity',])

    @test(depends_on=[SetupEnvironment.prepare_slaves_1],
          groups=["vcenter60_case_2", "vcenter60_simples"])
    @log_snapshot_on_error
    def test_case_2(self):
        """Deploy cluster with controller node only

        Scenario:
            1. Create cluster
            2. Add 1 node with controller role
            3. Deploy the cluster
            4. Validate cluster was set up correctly, there are no dead
            5. Create instance and delete instance.

        """
        self.env.revert_snapshot("ready_with_1_slaves")

        # Configure cluster
        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=settings.DEPLOYMENT_MODE_SIMPLE,
            settings={
                'volumes_lvm': False,
                'volumes_vmdk': True,
                'use_vcenter': True,
                'host_ip': settings.VCENTER_IP,
                'vc_user': settings.VCENTER_USERNAME,
                'vc_password': settings.VCENTER_PASSWORD,
                'cluster': settings.VCENTER_CLUSTERS
            }
        )
        logger.info("cluster is {}".format(cluster_id))

        # Add nodes to roles
        self.fuel_web.update_nodes(
            cluster_id,
            {'slave-01': ['controller', 'cinder']}
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)

        self.fuel_web.run_ostf(
            cluster_id=cluster_id, test_sets=['smoke', 'sanity'])
