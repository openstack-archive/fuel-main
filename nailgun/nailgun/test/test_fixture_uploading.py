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

import cStringIO

from nailgun.api.models import Node
from nailgun.api.models import Release
from nailgun.fixtures.fixman import upload_fixture
from nailgun.test.base import BaseIntegrationTest


class TestFixture(BaseIntegrationTest):

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
                "operating_system": "CentOS",
                "networks_metadata": [
                    {"name": "floating", "access": "public"},
                    {"name": "management", "access": "private192"},
                    {"name": "storage", "access": "private192"},
                    {"name": "fixed", "access": "private10"}
                ]
            }
        }]'''

        upload_fixture(cStringIO.StringIO(data))
        check = self.db.query(Release).filter(
            Release.name == u"CustomFixtureRelease"
        )
        self.assertEqual(len(list(check)), 1)
