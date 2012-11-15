# -*- coding: utf-8 -*-

import unittest
import json
from paste.fixture import TestApp

from nailgun.test.base import BaseHandlers
from nailgun.test.base import reverse


class TestHandlers(BaseHandlers):

    def test_notification_get_without_cluster(self):
        notification = self.create_default_notification()
        resp = self.app.get(
            reverse(
                'NotificationHandler',
                kwargs={'notification_id': notification.id}
            ),
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
        response = json.loads(resp.body)
        self.assertEquals(response.get('cluster', 'Iefah7th'), 'Iefah7th')
        self.assertEquals(notification.status, 'unread')
        self.assertEquals(notification.id, response['id'])
        self.assertEquals(notification.status, response['status'])
        self.assertEquals(notification.topic, response['topic'])
        self.assertEquals(notification.message, response['message'])

    def test_notification_get_with_cluster(self):
        cluster = self.create_default_cluster()
        notification = self.create_default_notification(cluster_id=cluster.id)
        resp = self.app.get(
            reverse(
                'NotificationHandler',
                kwargs={'notification_id': notification.id}
            ),
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
        response = json.loads(resp.body)
        self.assertEquals(response.get('cluster', 'Iefah7th'), cluster.id)
        self.assertEquals(notification.status, 'unread')
        self.assertEquals(notification.id, response['id'])
        self.assertEquals(notification.status, response['status'])
        self.assertEquals(notification.topic, response['topic'])
        self.assertEquals(notification.message, response['message'])

    def test_notification_update(self):
        notification = self.create_default_notification()
        notification_update = {
            'status': 'read'
        }
        resp = self.app.put(
            reverse(
                'NotificationHandler',
                kwargs={'notification_id': notification.id}
            ),
            json.dumps(notification_update),
            headers=self.default_headers
        )
        response = json.loads(resp.body)
        self.assertEquals(notification.id, response['id'])
        self.assertEquals('read', response['status'])
        self.assertEquals(notification.topic, response['topic'])
        self.assertEquals(notification.message, response['message'])

    def test_notification_not_found(self):
        notification = self.create_default_notification()
        resp = self.app.get(
            reverse(
                'NotificationHandler',
                kwargs={'notification_id': notification.id + 1}
            ),
            headers=self.default_headers,
            expect_errors=True
        )
        self.assertEquals(404, resp.status)
