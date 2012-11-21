# -*- coding: utf-8 -*-
import json
from paste.fixture import TestApp
from nailgun.api.models import Cluster
from nailgun.api.models import Node
from nailgun.api.models import Release
from nailgun.api.models import Attributes

from nailgun.test.base import BaseHandlers
from nailgun.test.base import reverse


class TestAttributes(BaseHandlers):

    def test_attributes_creation(self):
        cluster = self.create_cluster_api()
        resp = self.app.get(
            reverse(
                'ClusterAttributesHandler',
                kwargs={'cluster_id': cluster['id']}),
            headers=self.default_headers
        )
        release = self.db.query(Release).get(
            cluster['release']['id']
        )
        self.assertEquals(200, resp.status)
        self.assertEquals(
            json.loads(resp.body)['editable'],
            release.attributes_metadata['editable']
        )
        response = json.loads(resp.body)
        attrs = self.db.query(Attributes).filter(
            Attributes.cluster_id == cluster['id']
        ).first()
        self._compare(
            release.attributes_metadata['generated'],
            attrs.generated
        )

    def test_500_if_no_attributes(self):
        cluster = self.create_default_cluster()
        resp = self.app.put(
            reverse(
                'ClusterAttributesHandler',
                kwargs={'cluster_id': cluster.id}),
            params=json.dumps({
                'editable': {
                    "foo": "bar"
                },
            }),
            headers=self.default_headers,
            expect_errors=True
        )
        self.assertEquals(500, resp.status)

    def test_attributes_update(self):
        cluster_id = self.create_cluster_api()['id']
        resp = self.app.get(
            reverse(
                'ClusterAttributesHandler',
                kwargs={'cluster_id': cluster_id}),
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
        resp = self.app.put(
            reverse(
                'ClusterAttributesHandler',
                kwargs={'cluster_id': cluster_id}),
            params=json.dumps({
                'editable': {
                    "foo": "bar"
                },
            }),
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
        attrs = self.db.query(Attributes).filter(
            Attributes.cluster_id == cluster_id
        ).first()
        self.assertEquals("bar", attrs.editable["foo"])
        # 400 on generated update
        resp = self.app.put(
            reverse(
                'ClusterAttributesHandler',
                kwargs={'cluster_id': cluster_id}),
            params=json.dumps({
                'generated': {
                    "foo": "bar"
                },
            }),
            headers=self.default_headers,
            expect_errors=True
        )
        self.assertEquals(400, resp.status)
        # 400 if editable is not dict
        resp = self.app.put(
            reverse(
                'ClusterAttributesHandler',
                kwargs={'cluster_id': cluster_id}),
            params=json.dumps({
                'editable': ["foo", "bar"],
            }),
            headers=self.default_headers,
            expect_errors=True
        )
        self.assertEquals(400, resp.status)

    def test_attributes_set_defaults(self):
        cluster = self.create_cluster_api()
        # Change editable attributes.
        resp = self.app.put(
            reverse(
                'ClusterAttributesHandler',
                kwargs={'cluster_id': cluster['id']}),
            params=json.dumps({
                'editable': {
                    "foo": "bar"
                },
            }),
            headers=self.default_headers,
            expect_errors=True
        )
        self.assertEquals(200, resp.status)
        attrs = self.db.query(Attributes).filter(
            Attributes.cluster_id == cluster['id']
        ).first()
        self.assertEquals("bar", attrs.editable["foo"])
        # Set attributes to defaults.
        resp = self.app.put(
            reverse(
                'ClusterAttributesDefaultsHandler',
                kwargs={'cluster_id': cluster['id']}),
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
        release = self.db.query(Release).get(
            cluster['release']['id']
        )
        self.assertEquals(
            json.loads(resp.body)['editable'],
            release.attributes_metadata['editable']
        )

    def _compare(self, d1, d2):
        if isinstance(d1, dict) and isinstance(d2, dict):
            for s_field, s_value in d1.iteritems():
                if s_field not in d2:
                    raise KeyError()
                self._compare(s_value, d2[s_field])
        elif isinstance(d1, str) or isinstance(d1, unicode):
            if d1 in [u"", ""]:
                self.assertEqual(len(d2), 8)
            else:
                self.assertEqual(d1, d2)
