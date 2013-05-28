# -*- coding: utf-8 -*-
import json
import unittest
from paste.fixture import TestApp

from mock import patch
from sqlalchemy.sql import not_

from nailgun.api.models import Release, Network
from nailgun.test.base import BaseHandlers
from nailgun.test.base import reverse


class TestHandlers(BaseHandlers):
    def test_cluster_list_empty(self):
        resp = self.app.get(
            reverse('ClusterCollectionHandler'),
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
        response = json.loads(resp.body)
        self.assertEquals([], response)

    def test_cluster_create(self):
        release_id = self.env.create_release(api=False).id
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
        nets = self.db.query(Network).filter(
            not_(Network.name == "fuelweb_admin")
        ).all()
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
        self.assertItemsEqual(expected, obtained)

    def test_network_validation_on_cluster_creation(self):
        cluster = self.env.create_cluster(api=True)
        nets = self.env.generate_ui_networks(cluster["id"])
        nets['networks'][-1]["network_size"] = 16
        nets['networks'][-1]["amount"] = 3
        resp = self.app.put(
            reverse('NetworkConfigurationHandler',
                    kwargs={'cluster_id': cluster['id']}),
            json.dumps(nets),
            headers=self.default_headers,
            expect_errors=True
        )
        self.assertEquals(202, resp.status)
        task = json.loads(resp.body)
        self.assertEquals(task['status'], 'error')

    @patch('nailgun.rpc.cast')
    def test_verify_networks(self, mocked_rpc):
        cluster = self.env.create_cluster(api=True)
        resp = self.app.put(
            reverse('NetworkConfigurationHandler',
                    kwargs={'cluster_id': cluster['id']}),
            json.dumps(self.env.generate_ui_networks(cluster["id"])),
            headers=self.default_headers
        )
        self.assertEquals(202, resp.status)
        task = json.loads(resp.body)
        self.assertEquals(task['status'], 'ready')
