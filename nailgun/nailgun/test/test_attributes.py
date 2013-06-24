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
from nailgun.api.models import Cluster
from nailgun.api.models import Node
from nailgun.api.models import Release
from nailgun.api.models import Attributes

from nailgun.test.base import BaseHandlers
from nailgun.test.base import reverse


class TestAttributes(BaseHandlers):

    def test_attributes_creation(self):
        cluster = self.env.create_cluster(api=True)
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
        cluster = self.env.create_cluster(api=False)
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
        cluster_id = self.env.create_cluster(api=True)['id']
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

    def test_get_default_attributes(self):
        cluster = self.env.create_cluster(api=True)
        release = self.db.query(Release).get(
            cluster['release']['id']
        )
        resp = self.app.put(
            reverse(
                'ClusterAttributesDefaultsHandler',
                kwargs={'cluster_id': cluster['id']}),
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
        self.assertEquals(
            json.loads(resp.body)['editable'],
            release.attributes_metadata['editable']
        )

    def test_attributes_set_defaults(self):
        cluster = self.env.create_cluster(api=True)
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

    def test_attributes_merged_values(self):
        cluster = self.env.create_cluster(api=True)
        cluster_db = self.db.query(Cluster).get(cluster['id'])
        orig_attrs = cluster_db.attributes.merged_attrs()
        attrs = cluster_db.attributes.merged_attrs_values()
        for group, group_attrs in orig_attrs.iteritems():
            for attr, orig_value in group_attrs.iteritems():
                if group == 'common':
                    value = attrs[attr]
                else:
                    value = attrs[group][attr]
                if isinstance(orig_value, dict) and 'value' in orig_value:
                    self.assertEquals(orig_value['value'], value)
                else:
                    self.assertEquals(orig_value, value)

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
