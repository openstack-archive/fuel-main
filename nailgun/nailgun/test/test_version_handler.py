# -*- coding: utf-8 -*-

import json
import logging
import unittest
from mock import patch

from nailgun.settings import settings
from nailgun.test.base import BaseHandlers
from nailgun.test.base import reverse
from nailgun.network import manager as netmanager
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
            {"release": "0.1b", "sha": "12345"}
        )
