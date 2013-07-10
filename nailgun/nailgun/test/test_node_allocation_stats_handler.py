# -*- coding: utf-8 -*-

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
