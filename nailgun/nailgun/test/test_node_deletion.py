import logging

from mock import patch

from nailgun.test.base import BaseHandlers
from nailgun.test.base import reverse
from nailgun.api.models import Network, Node, NetworkElement

logger = logging.getLogger(__name__)


class TestNodeDeletion(BaseHandlers):

    @patch('nailgun.rpc.cast')
    def test_node_deletion_and_attributes_clearing(self, mocked_rpc):
        cluster = self.create_cluster_api()
        node = self.create_default_node(cluster_id=cluster['id'],
                                        pending_deletion=True)

        with patch('nailgun.task.task.Cobbler'):
            resp = self.app.put(
                reverse(
                    'ClusterChangesHandler',
                    kwargs={'cluster_id': unicode(cluster['id'])}),
                headers=self.default_headers
            )
            self.assertEquals(200, resp.status)

        resp = self.app.delete(
            reverse(
                'NodeHandler',
                kwargs={'node_id': node.id}),
            headers=self.default_headers
        )
        self.assertEquals(204, resp.status)

        node_try = self.db.query(Node).filter_by(
            cluster_id=cluster['id']
        ).first()
        self.assertEquals(node_try, None)

        management_net = self.db.query(Network).filter_by(
            cluster_id=cluster['id']).filter_by(
                name='management').first()

        ipaddrs = [x for x in self.db.query(NetworkElement).filter_by(
            node=node.id).all() if x.ip_addr]

        self.assertEquals(list(management_net.nodes), [])
        self.assertEquals(list(ipaddrs), [])
