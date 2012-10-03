# -*- coding: utf-8 -*-
import json
from paste.fixture import TestApp

from api.models import Release, Network
from base import BaseHandlers
from base import reverse


class TestHandlers(BaseHandlers):
    def test_cluster_list_empty(self):
        resp = self.app.get(
            reverse('ClusterCollectionHandler'),
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
        response = json.loads(resp.body)
        self.assertEquals([], response)

    def test_cluster_list_big(self):
        for i in range(100):
            self.create_default_cluster()
        resp = self.app.get(
            reverse('ClusterCollectionHandler'),
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
        response = json.loads(resp.body)
        self.assertEquals(100, len(response))

    def test_cluster_create(self):
        release_id = self.create_default_release().id
        resp = self.app.post(
            reverse('ClusterCollectionHandler'),
            json.dumps({
                'name': 'cluster-name',
                'release': release_id,
            }),
            headers=self.default_headers
        )
        self.assertEquals(201, resp.status)

    def test_if_cluster_creates_correct_networks(self):
        release = Release()
        release.version = "1.1.1"
        release.name = u"release_name_" + str(release.version)
        release.description = u"release_desc" + str(release.version)
        release.networks_metadata = [
            {"name": "floating", "access": "public"},
            {"name": "fixed", "access": "private10"},
            {"name": "storage", "access": "private192"},
            {"name": "management", "access": "private172"},
            {"name": "other_172", "access": "private172"},
        ]
        release.attributes_metadata = {
            "editable": {
                "keystone": {
                    "admin_tenant": "admin"
                }
            },
            "generated": {
                "mysql": {
                    "root_password": ""
                }
            }
        }
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
        nets = self.db.query(Network).all()
        obtained = []
        for net in nets:
            obtained.append({
                'release': net.release,
                'name': net.name,
                'access': net.access,
                'vlan_id': net.vlan_id,
                'cidr': net.cidr,
                'gateway': net.gateway
            })
        expected = [
            {
                'release': release.id,
                'name': u'floating',
                'access': 'public',
                'vlan_id': 100,
                'cidr': '240.0.0.0/24',
                'gateway': '240.0.0.1'
            },
            {
                'release': release.id,
                'name': u'fixed',
                'access': 'private10',
                'vlan_id': 101,
                'cidr': '10.0.0.0/24',
                'gateway': '10.0.0.1'
            },
            {
                'release': release.id,
                'name': u'storage',
                'access': 'private192',
                'vlan_id': 102,
                'cidr': '192.168.0.0/24',
                'gateway': '192.168.0.1'
            },
            {
                'release': release.id,
                'name': u'management',
                'access': 'private172',
                'vlan_id': 103,
                'cidr': '172.16.0.0/24',
                'gateway': '172.16.0.1'
            },
            {
                'release': release.id,
                'name': u'other_172',
                'access': 'private172',
                'vlan_id': 104,
                'cidr': '172.16.1.0/24',
                'gateway': '172.16.1.1'
            },
        ]
        self.assertEquals(expected, obtained)

    def test_verify_networks(self):
        cluster = self.create_cluster_api()
        resp = self.app.put(
            reverse('ClusterNetworksHandler',
                    kwargs={'cluster_id': cluster['id']}),
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
