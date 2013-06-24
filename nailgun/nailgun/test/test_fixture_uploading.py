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
import cStringIO

from nailgun.test.base import BaseHandlers
from nailgun.fixtures.fixman import upload_fixture
from nailgun.api.models import Release, Node


class TestFixture(BaseHandlers):

    fixtures = ['sample_environment']

    def test_upload_working(self):
        check = self.db.query(Node).all()
        self.assertEqual(len(list(check)), 8)

    def test_custom_fixture(self):
        data = '''[{
            "pk": 2,
            "model": "nailgun.release",
            "fields": {
                "name": "CustomFixtureRelease",
                "version": "0.0.1",
                "description": "Sample release for testing",
                "networks_metadata": [
                  {"name": "floating", "access": "public"},
                  {"name": "fixed", "access": "private10"},
                  {"name": "management", "access": "private172"},
                  {"name": "storage", "access": "private192"}
                ]
            }
        }]'''

        upload_fixture(cStringIO.StringIO(data))
        check = self.db.query(Release).filter(
            Release.name == u"CustomFixtureRelease"
        )
        self.assertEqual(len(list(check)), 1)
