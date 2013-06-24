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


# -*- coding: utf-8 -*-

import unittest
import json

from nailgun.test.base import BaseHandlers
from nailgun.test.base import reverse


class TestHandlers(BaseHandlers):
    def test_all_api_urls_404_or_405(self):
        urls = {
            'ClusterHandler': {'cluster_id': 1},
            'NodeHandler': {'node_id': 1},
            'ReleaseHandler': {'release_id': 1},
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
