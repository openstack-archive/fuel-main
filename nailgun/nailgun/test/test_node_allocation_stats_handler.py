import json

from nailgun.test.base import BaseHandlers, reverse


class TestHandlers(BaseHandlers):
    def _get_allocation_stats(self):
        resp = self.app.get(
            reverse('NodesAllocationStatsHandler'))
        return json.loads(resp.body)

    def test_allocation_stats_unallocated(self):
        node = self.env.create_node(api=False)
        stats = self._get_allocation_stats()
        self.assertEquals(stats['total'], 1)
        self.assertEquals(stats['unallocated'], 1)

    def test_allocation_stats_total(self):
        node = self.env.create_node(api=False)
        self.env.create(
            cluster_kwargs={},
            nodes_kwargs=[
                {
                    "pending_addition": True,
                }
            ]
        )

        stats = self._get_allocation_stats()
        self.assertEquals(stats['total'], 2)
        self.assertEquals(stats['unallocated'], 1)
