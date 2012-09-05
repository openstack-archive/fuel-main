# -*- coding: utf-8 -*-
import json
from paste.fixture import TestApp
from api.models import Release
from base import BaseHandlers
from base import reverse


class TestHandlers(BaseHandlers):
    def test_release_put_change_name_and_version(self):
        release = self.create_default_release()
        resp = self.app.put(
            reverse('ReleaseHandler', kwargs={'release_id': release.id}),
            params=json.dumps({
                'name': 'modified release',
                'version': '5.1'
            }),
            headers=self.default_headers,
            expect_errors=True)
        self.assertEquals(200, resp.status)
        response = json.loads(resp.body)
        release_from_db = self.db.query(Release).one()
        self.db.refresh(release_from_db)
        self.assertEquals('5.1', release_from_db.version)
        self.assertEquals('5.1', response['version'])
        self.assertEquals('modified release', response['name'])

    def test_release_put_returns_400_if_no_body(self):
        release = self.create_default_release()
        resp = self.app.put(
            reverse('ReleaseHandler', kwargs={'release_id': release.id}),
            "",
            headers=self.default_headers,
            expect_errors=True)
        self.assertEquals(resp.status, 400)

    def test_release_delete(self):
        release = self.create_default_release()
        resp = self.app.delete(
            reverse('ReleaseHandler', kwargs={'release_id': release.id}),
            params=json.dumps({
                'name': 'Another test release',
                'version': '1.0'
            }),
            headers=self.default_headers
        )
        self.assertEquals(204, resp.status)
        self.assertEquals('', resp.body)

    def test_release_create(self):
        resp = self.app.post(
            reverse('ReleaseCollectionHandler'),
            params=json.dumps({
                'name': 'Another test release',
                'version': '1.0'
            }),
            headers=self.default_headers
        )
        self.assertEquals(resp.status, 201)

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
                    {"name": "fixed", "access": "private"},
                    {"name": "storage", "access": "private"}
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
                    {"name": "fixed", "access": "private"}
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
