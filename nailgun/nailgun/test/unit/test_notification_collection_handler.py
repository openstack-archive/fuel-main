# -*- coding: utf-8 -*-

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

import json

from nailgun.api.models import Notification
from nailgun.test.base import BaseIntegrationTest
from nailgun.test.base import reverse


class TestHandlers(BaseIntegrationTest):

    def test_empty(self):
        resp = self.app.get(
            reverse('NotificationCollectionHandler'),
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
        response = json.loads(resp.body)
        self.assertEquals([], response)

    def test_not_empty(self):
        c = self.env.create_cluster(api=False)
        n0 = self.env.create_notification()
        n1 = self.env.create_notification(cluster_id=c.id)
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

    def test_get_limit(self):
        self.env.create_cluster(api=False)
        for i in xrange(3):
            self.env.create_notification()

        resp = self.app.get(
            reverse('NotificationCollectionHandler'),
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
        response = json.loads(resp.body)
        notifications_count = self.db.query(Notification).count()
        self.assertEquals(notifications_count, 3)

        resp = self.app.get(
            reverse('NotificationCollectionHandler'),
            params={'limit': 2},
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
        response = json.loads(resp.body)
        self.assertEquals(len(response), 2)

    def test_update(self):
        c = self.env.create_cluster(api=False)
        n0 = self.env.create_notification()
        n1 = self.env.create_notification(cluster_id=c.id)
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
