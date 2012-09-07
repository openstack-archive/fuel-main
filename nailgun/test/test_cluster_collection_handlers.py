# -*- coding: utf-8 -*-
import json
from paste.fixture import TestApp
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

    #def test_if_cluster_creates_correct_networks(self):
        #pass
