# -*- coding: utf-8 -*-
import json

from api.models import Release, Network
from base import BaseHandlers
from base import reverse


class TestHandlers(BaseHandlers):
    def test_nets_empty(self):
        resp = self.app.get(
            reverse('NetworkCollectionHandler'),
            headers=self.default_headers,
            expect_errors=True
        )
        self.assertEquals(404, resp.status)

    def test_valid_nets_returned_after_cluster_create(self):
        release = Release()
        release.version = "2.2.1"
        release.name = u"release_name_" + str(release.version)
        release.description = u"release_desc" + str(release.version)
        release.networks_metadata = [
            {"name": "floating", "access": "public"},
            {"name": "fixed", "access": "private10"},
            {"name": "storage", "access": "private192"},
            {"name": "management", "access": "private172"},
            {"name": "other_172", "access": "private172"},
        ]
        self.db.add(release)
        self.db.commit()
        resp = self.app.post(
            reverse('ClusterCollectionHandler'),
            json.dumps({
                'name': 'cluster-name',
                'release': release.id,
            }),
            headers=self.default_headers
        )
        self.assertEquals(201, resp.status)
        resp = self.app.get(
            reverse('NetworkCollectionHandler'),
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
        response = json.loads(resp.body)

        expected = [
            {
                'id': 1,
                #'release': release.id,
                'name': u'floating',
                'access': 'public',
                'vlan_id': 100,
                'cidr': '240.0.0.0/24',
                'gateway': '240.0.0.1'
            },
            {
                'id': 2,
                #'release': release.id,
                'name': u'fixed',
                'access': 'private10',
                'vlan_id': 101,
                'cidr': '10.0.0.0/24',
                'gateway': '10.0.0.1'
            },
            {
                'id': 3,
                #'release': release.id,
                'name': u'storage',
                'access': 'private192',
                'vlan_id': 102,
                'cidr': '192.168.0.0/24',
                'gateway': '192.168.0.1'
            },
            {
                'id': 4,
                #'release': release.id,
                'name': u'management',
                'access': 'private172',
                'vlan_id': 103,
                'cidr': '172.16.0.0/24',
                'gateway': '172.16.0.1'
            },
            {
                'id': 5,
                #'release': release.id,
                'name': u'other_172',
                'access': 'private172',
                'vlan_id': 104,
                'cidr': '172.16.1.0/24',
                'gateway': '172.16.1.1'
            },
        ]
        self.assertEquals(expected, response)
