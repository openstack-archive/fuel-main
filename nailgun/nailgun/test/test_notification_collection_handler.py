# -*- coding: utf-8 -*-

import unittest
import json
from paste.fixture import TestApp

from nailgun.test.base import BaseHandlers
from nailgun.test.base import reverse


class TestHandlers(BaseHandlers):

    def test_empty(self):
        resp = self.app.get(
            reverse('NotificationCollectionHandler'),
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
        response = json.loads(resp.body)
        self.assertEquals([], response)

    def test_not_empty(self):
        c = self.create_default_cluster()
        n0 = self.create_default_notification()
        n1 = self.create_default_notification(cluster_id=c.id)
        resp = self.app.get(
            reverse('NotificationCollectionHandler'),
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
        response = json.loads(resp.body)
        self.assertEquals(len(response), 2)
        if response[0]['id'] == n0.id:
            rn0 = response[0]
            rn1 = response[1]
        else:
            rn0 = response[1]
            rn1 = response[0]
        self.assertEquals(rn1['cluster'], n1.cluster_id)
        self.assertIsNone(rn0.get('cluster', None))

    def test_update(self):
        c = self.create_default_cluster()
        n0 = self.create_default_notification()
        n1 = self.create_default_notification(cluster_id=c.id)
        notification_update = [
            {
                'id': n0.id,
                'status': 'read'
            },
            {
                'id': n1.id,
                'status': 'read'
            }
        ]
        resp = self.app.put(
            reverse('NotificationCollectionHandler'),
            json.dumps(notification_update),
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
        response = json.loads(resp.body)
        self.assertEquals(len(response), 2)
        if response[0]['id'] == n0.id:
            rn0 = response[0]
            rn1 = response[1]
        else:
            rn0 = response[1]
            rn1 = response[0]
        self.assertEquals(rn1['cluster'], n1.cluster_id)
        self.assertEquals(rn1['status'], 'read')
        self.assertIsNone(rn0.get('cluster', None))
        self.assertEquals(rn0['status'], 'read')
