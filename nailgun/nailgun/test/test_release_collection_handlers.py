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
from paste.fixture import TestApp

from nailgun.api.models import Release
from nailgun.test.base import BaseHandlers
from nailgun.test.base import reverse


class TestHandlers(BaseHandlers):
    def test_release_list_empty(self):
        resp = self.app.get(
            reverse('ReleaseCollectionHandler'),
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
        response = json.loads(resp.body)
        self.assertEquals([], response)

    def test_release_creation(self):
        resp = self.app.post(
            reverse('ReleaseCollectionHandler'),
            params=json.dumps({
                'name': 'Another test release',
                'version': '1.0'
            }),
            headers=self.default_headers
        )
        self.assertEquals(resp.status, 201)

    def test_release_create(self):
        release_name = "OpenStack"
        release_version = "1.0.0"
        release_description = "This is test release"
        resp = self.app.post(
            reverse('ReleaseCollectionHandler'),
            json.dumps({
                'name': release_name,
                'version': release_version,
                'description': release_description,
                'networks_metadata': [
                    {"name": "floating", "access": "public"},
                    {"name": "fixed", "access": "private10"},
                    {"name": "storage", "access": "private192"}
                ]
            }),
            headers=self.default_headers
        )
        self.assertEquals(resp.status, 201)

        resp = self.app.post(
            reverse('ReleaseCollectionHandler'),
            json.dumps({
                'name': release_name,
                'version': release_version,
                'description': release_description,
                'networks_metadata': [
                    {"name": "fixed", "access": "private10"}
                ]
            }),
            headers=self.default_headers,
            expect_errors=True
        )
        self.assertEquals(resp.status, 409)

        release_from_db = self.db.query(Release).filter_by(
            name=release_name,
            version=release_version,
            description=release_description
        ).all()
        self.assertEquals(len(release_from_db), 1)

    def test_release_create_already_exist(self):
        release_name = "OpenStack"
        release_version = "1.0.0"
        release_description = "This is test release"
        resp = self.app.post(
            reverse('ReleaseCollectionHandler'),
            json.dumps({
                'name': release_name,
                'version': release_version,
                'description': release_description,
                'networks_metadata': [
                    {"name": "floating", "access": "public"},
                    {"name": "fixed", "access": "private10"},
                    {"name": "storage", "access": "private192"}
                ]
            }),
            headers=self.default_headers
        )
        self.assertEquals(resp.status, 201)

        resp = self.app.post(
            reverse('ReleaseCollectionHandler'),
            json.dumps({
                'name': release_name,
                'version': release_version,
                'description': release_description,
                'networks_metadata': [
                    {"name": "fixed", "access": "private10"}
                ]
            }),
            headers=self.default_headers,
            expect_errors=True
        )
        self.assertEquals(resp.status, 409)

        release_from_db = self.db.query(Release).filter(
            Release.name == release_name,
            Release.version == release_version,
            Release.description == release_description
        ).one()
