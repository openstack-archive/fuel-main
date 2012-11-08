import logging

from mock import patch

from nailgun.test.base import BaseHandlers
from nailgun.test.base import reverse
from nailgun.api.models import Network, Node, IPAddr

logger = logging.getLogger(__name__)


class TestNodeDeletion(BaseHandlers):

    def test_node_deletion_and_attributes_clearing(self):
        cluster = self.create_cluster_api()
        node = self.create_default_node(cluster_id=cluster['id'])

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

        ipaddrs = self.db.query(IPAddr).filter_by(node=node.id).all()

        self.assertEquals(list(management_net.nodes), [])
        self.assertEquals(list(ipaddrs), [])
