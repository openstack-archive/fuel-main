# -*- coding: utf-8 -*-
import unittest
import json
from paste.fixture import TestApp
from api.models import Release
from base import BaseHandlers
from base import reverse


class TestHandlers(BaseHandlers):

    def test_release_creation(self):
        resp = self.app.post(
            '/api/releases',
            params=json.dumps({
                'name': 'Another test release',
                'version': '1.0'
            }),
            headers=self.default_headers
        )
        self.assertEquals(resp.status, 201)

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
            self.assertTrue(resp.status in [404,405])
            resp = self.app.delete(test_url, expect_errors=True)
            self.assertTrue(resp.status in [404,405])
            resp = self.app.put(test_url, expect_errors=True)
            self.assertTrue(resp.status in [404,405])
            resp = self.app.post(test_url, expect_errors=True)
            self.assertTrue(resp.status in [404,405])

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
        ).all()
        self.assertEquals(len(release_from_db), 1)

    @unittest.skip("obsolete")
    def test_network_create(self):
        network_data = {
            "name": "test_network",
            "network": "10.0.0.0/24",
            "range_l": "10.0.0.5",
            "range_h": "10.0.0.10",
            "gateway": "10.0.0.1",
            "vlan_id": 100,
            "release": 1,
            "access": "public"
        }
        resp = self.app.post(
            reverse('NetworkCollectionHandler'),
            json.dumps(network_data),
            headers=self.default_headers
        )
        self.assertEquals(resp.status, 201)
        resp = self.app.post(
            reverse('NetworkCollectionHandler'),
            json.dumps(network_data),
            headers=self.default_headers,
            expect_errors=True
        )
        self.assertEquals(resp.status, 409)
        network_data["network"] = "test_fail"
        resp = self.app.post(
            reverse('NetworkCollectionHandler'),
            json.dumps(network_data),
            headers=self.default_headers,
            expect_errors=True
        )
        self.assertEqual(resp.status, 400)
