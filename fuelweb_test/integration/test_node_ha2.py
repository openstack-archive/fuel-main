import logging
import unittest
from fuelweb_test.integration.base_node_test_case import BaseNodeTestCase
from fuelweb_test.integration.decorators import snapshot_errors, \
    debug, fetch_logs

logging.basicConfig(
    format=':%(lineno)d: %(asctime)s %(message)s',
    level=logging.DEBUG
)

logger = logging.getLogger(__name__)
logwrap = debug(logger)


class TestNode(BaseNodeTestCase):
    @snapshot_errors
    @logwrap
    @fetch_logs
    def test_ha_cluster_flat(self):
        cluster_name = 'ha_flat'
        nodes = {
            'controller': ['slave-01', 'slave-02', 'slave-03'],
            'compute': ['slave-04', 'slave-05']
        }
        cluster_id = self._basic_provisioning(cluster_name, nodes)
        self.assertClusterReady(
            'slave-01', smiles_count=13, networks_count=1, timeout=300)
        self.get_ebtables(cluster_id, self.nodes().slaves[:5]).restore_vlans()
        task = self._run_network_verify(cluster_id)
        self.assertTaskSuccess(task, 60 * 2)

if __name__ == '__main__':
    unittest.main()
