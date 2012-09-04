# -*- coding: utf-8 -*-
import json
from paste.fixture import TestApp
from base import BaseHandlers
from base import reverse


class TestHandlers(BaseHandlers):

    def test_node_list_empty(self):
        resp = self.app.get(
            reverse('NodeCollectionHandler'),
            headers = self.default_headers
        )
        self.assertEquals(200, resp.status)
        response = json.loads(resp.body)
        self.assertEquals([], response)

    def test_node_list_big(self):
        for i in range(100):
            self.create_default_node()
        resp = self.app.get(
            reverse('NodeCollectionHandler'),
            headers = self.default_headers
        )
        self.assertEquals(200, resp.status)
        response = json.loads(resp.body)
        self.assertEquals(100, len(response))

