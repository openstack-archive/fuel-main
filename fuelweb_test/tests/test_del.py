from fuelweb_test.tests.test_simple import SimpleFlat

__author__ = 'alan'


import re

from devops.helpers.helpers import wait
from proboscis.asserts import assert_equal
from proboscis.asserts import assert_true
from proboscis import test

from fuelweb_test.helpers.decorators import log_snapshot_on_error
from fuelweb_test.helpers.eb_tables import Ebtables
from fuelweb_test.settings import DEPLOYMENT_MODE_SIMPLE
from fuelweb_test.settings import NODE_VOLUME_SIZE
from fuelweb_test.tests.base_test_case import SetupEnvironment
from fuelweb_test.tests.base_test_case import TestBasic
from fuelweb_test import logger

@test(groups=["thread_2", "test"])
class DeleteEnvironment(TestBasic):
    @test(depends_on=[SimpleFlat.deploy_simple_flat],
          groups=["delete_environment1"])
    @log_snapshot_on_error
    def delete_environment(self):
        """Delete existing environment
        and verify nodes returns to unallocated state

        Scenario:
            1. Revert "simple flat" environment
            2. Delete environment
            2. Delete environment
            3. Verify node returns to unallocated pull

        """
        self.env.revert_snapshot("deploy_simple_flat")

        cluster_id = self.fuel_web.get_last_created_cluster()
        self.fuel_web.client.delete_cluster(cluster_id)
        nailgun_nodes = self.fuel_web.client.list_nodes()
        nodes = filter(lambda x: x["pending_deletion"] is True, nailgun_nodes)
        assert_true(
            len(nodes) == 2, "Verify 2 node has pending deletion status"
        )
        wait(
            lambda:
            self.fuel_web.is_node_discovered(nodes[0]) and
            self.fuel_web.is_node_discovered(nodes[1]),
            timeout=10 * 60,
            interval=15
        )