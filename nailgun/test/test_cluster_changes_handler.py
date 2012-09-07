import json

from base import BaseHandlers
from base import reverse


class TestClusterChangesHandler(BaseHandlers):
    def test_cluster_starts_deploy(self):
        cluster = self.create_default_cluster()
        resp = self.app.put(
            reverse(
                'ClusterChangesHandler',
                kwargs={'cluster_id': cluster.id}),
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
