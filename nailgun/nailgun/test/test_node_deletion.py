import logging

from mock import Mock, patch

import nailgun
from nailgun.test.base import BaseHandlers
from nailgun.test.base import reverse
from nailgun.api.models import Node, IPAddr
from nailgun.api.models import Network, NetworkGroup

logger = logging.getLogger(__name__)


class TestNodeDeletion(BaseHandlers):

    @patch('nailgun.rpc.cast')
    def test_node_deletion_and_attributes_clearing(self, mocked_rpc):
        self.env.create(
            cluster_kwargs={},
            nodes_kwargs=[
                {"pending_addition": True},
            ]
        )

        with patch('nailgun.task.task.Cobbler'):
            self.env.launch_deployment()

        cluster = self.env.clusters[0]
        node = self.env.nodes[0]

        resp = self.app.delete(
            reverse(
                'NodeHandler',
                kwargs={'node_id': node.id}),
            headers=self.default_headers
        )
        self.assertEquals(204, resp.status)

        node_try = self.db.query(Node).filter_by(
            cluster_id=cluster.id
        ).first()
        self.assertEquals(node_try, None)

        management_net = self.db.query(Network).join(NetworkGroup).\
            filter(NetworkGroup.cluster_id == cluster.id).filter_by(
                name='management').first()

        ipaddrs = self.db.query(IPAddr).filter_by(node=node.id).all()

        self.assertEquals(list(management_net.nodes), [])
        self.assertEquals(list(ipaddrs), [])
