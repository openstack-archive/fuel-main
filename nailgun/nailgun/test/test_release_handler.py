# -*- coding: utf-8 -*-
import json
from paste.fixture import TestApp

from nailgun.api.models import Release
from nailgun.test.base import BaseHandlers
from nailgun.test.base import reverse


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
