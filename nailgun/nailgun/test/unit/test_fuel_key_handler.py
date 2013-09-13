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

import base64
import json
from mock import patch

from nailgun.test.base import BaseTestCase
from nailgun.test.base import reverse


class TestFuelKeyHandler(BaseTestCase):

    @patch('nailgun.api.handlers.version.settings.PRODUCT_VERSION', '0.1b')
    @patch('nailgun.api.handlers.version.settings.COMMIT_SHA', '12345')
    @patch('nailgun.api.handlers.version.settings.FUEL_KEY', 'uuid')
    def test_version_handler(self):
        resp = self.app.get(
            reverse('FuelKeyHandler'),
            headers=self.default_headers
        )
        key_data = {"release": "0.1b", "sha": "12345", "uuid": "uuid"}
        signature = base64.b64encode(json.dumps(key_data))
        key_data["signature"] = signature

        self.assertEqual(200, resp.status)
        self.assertEqual(
            json.loads(resp.body),
            {"key": base64.b64encode(json.dumps(key_data))}
        )
