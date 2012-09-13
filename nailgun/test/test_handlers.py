# -*- coding: utf-8 -*-

import unittest
import json

from base import BaseHandlers
from base import reverse


class TestHandlers(BaseHandlers):
    def test_all_api_urls_404_or_405(self):
        urls = {
            'ClusterHandler': {'cluster_id': 1},
            'NodeHandler': {'node_id': 1},
            'ReleaseHandler': {'release_id': 1},
            'RoleHandler': {'role_id': 1},
        }
        for handler in urls:
            test_url = reverse(handler, urls[handler])
            resp = self.app.get(test_url, expect_errors=True)
            self.assertTrue(resp.status in [404, 405])
            resp = self.app.delete(test_url, expect_errors=True)
            self.assertTrue(resp.status in [404, 405])
            resp = self.app.put(test_url, expect_errors=True)
            self.assertTrue(resp.status in [404, 405])
            resp = self.app.post(test_url, expect_errors=True)
            self.assertTrue(resp.status in [404, 405])
