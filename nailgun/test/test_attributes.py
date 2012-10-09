# -*- coding: utf-8 -*-
import json
from paste.fixture import TestApp
from api.models import Cluster, Node, Attributes
from base import BaseHandlers
from base import reverse


class TestAttributes(BaseHandlers):

    def test_attributes_creation(self):
        release = self.create_default_release()
        yet_another_cluster_name = 'Yet another cluster'
        resp = self.app.post(
            '/api/clusters',
            params=json.dumps({
                'name': yet_another_cluster_name,
                'release': release.id
            }),
            headers=self.default_headers
        )
        self.assertEquals(201, resp.status)
        response = json.loads(resp.body)
        cluster_id = int(response["id"])
        resp = self.app.get(
            '/api/clusters/%d/attributes/' % cluster_id,
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
        self.assertEquals(
            json.loads(resp.body)['editable'],
            release.attributes_metadata['editable']
        )
        response = json.loads(resp.body)
        attrs = self.db.query(Attributes).filter(
            Attributes.cluster_id == cluster_id
        ).first()
        self._compare(
            release.attributes_metadata['generated'],
            attrs.generated
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
