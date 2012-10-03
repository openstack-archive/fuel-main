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
        response = json.loads(resp.body)
        attrs = self.db.query(Attributes).filter(
            Attributes.cluster_id == cluster_id
        ).first()
        for service, fields in attrs.editable.iteritems():
            for f, value in fields.iteritems():
                self.assertNotEqual(value, "")
