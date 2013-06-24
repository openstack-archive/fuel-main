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

import json
import logging
import unittest
from mock import patch

from nailgun.settings import settings
from nailgun.test.base import BaseHandlers
from nailgun.test.base import reverse
from nailgun.api.models import Cluster


class TestVersionHandler(BaseHandlers):

    @patch('nailgun.api.handlers.version.settings.PRODUCT_VERSION', '0.1b')
    @patch('nailgun.api.handlers.version.settings.COMMIT_SHA', '12345')
    def test_version_handler(self):
        resp = self.app.get(
            reverse('VersionHandler'),
            headers=self.default_headers
        )
        self.assertEqual(200, resp.status)
        self.assertEqual(
            json.loads(resp.body),
            {"release": "0.1b", "sha": "12345", "fuel_sha": "Unknown build"}
        )
