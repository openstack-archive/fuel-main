# -*- coding: utf-8 -*-

import time
import uuid
import json

import eventlet
eventlet.monkey_patch()

from nailgun.rpc import receiver as rec
from nailgun.test.base import BaseHandlers
from nailgun.api.models import Node, Task, Notification
from nailgun.test.base import reverse


class TestNotification(BaseHandlers):

    def test_notification_deploy_done(self):
        cluster = self.create_default_cluster()
        receiver = rec.NailgunReceiver()

        task = Task(
            uuid=str(uuid.uuid4()),
            name="super",
            cluster_id=cluster.id
        )
        self.db.add(task)
        self.db.commit()

        kwargs = {
            'task_uuid': task.uuid,
            'status': 'ready',
        }

        receiver.deploy_resp(**kwargs)

        notification = self.db.query(Notification).filter_by(
            cluster_id=cluster.id).first()

        self.assertEqual(notification.status, "unread")
        self.assertEqual(notification.topic, "done")

    def test_notification_deploy_error(self):
        cluster = self.create_default_cluster()
        receiver = rec.NailgunReceiver()

        task = Task(
            uuid=str(uuid.uuid4()),
            name="super",
            cluster_id=cluster.id
        )
        self.db.add(task)
        self.db.commit()

        kwargs = {
            'task_uuid': task.uuid,
            'status': 'error',
        }

        receiver.deploy_resp(**kwargs)

        notification = self.db.query(Notification).filter_by(
            cluster_id=cluster.id).first()

        self.assertEqual(notification.status, "unread")
        self.assertEqual(notification.topic, "error")

    def test_notification_node_discover(self):

        resp = self.app.post(
            reverse('NodeCollectionHandler'),
            json.dumps({'mac': 'AADFAAAADFAA',
                        'meta': self.default_metadata(),
                        'status': 'discover'}),
            headers=self.default_headers)
        self.assertEquals(resp.status, 201)

        notification = self.db.query(Notification).first()

        self.assertEquals(notification.status, 'unread')
        self.assertEquals(notification.topic, 'discover')

    def test_notification_delete_cluster_done(self):
        cluster = self.create_default_cluster()
        cluster_name = cluster.name
        receiver = rec.NailgunReceiver()

        task = Task(
            uuid=str(uuid.uuid4()),
            name="cluster_deletion",
            cluster_id=cluster.id
        )
        self.db.add(task)
        self.db.commit()

        kwargs = {
            'task_uuid': task.uuid,
            'status': 'ready',
        }

        receiver.remove_cluster_resp(**kwargs)

        notification = self.db.query(Notification).first()

        self.assertEqual(notification.status, "unread")
        self.assertEqual(notification.topic, "done")
        self.assertEqual(
            notification.message,
            "Installation '%s' and all its nodes "
            "are deleted" % cluster_name
        )

    def test_notification_delete_cluster_failed(self):
        cluster = self.create_default_cluster()
        receiver = rec.NailgunReceiver()

        task = Task(
            uuid=str(uuid.uuid4()),
            name="cluster_deletion",
            cluster_id=cluster.id
        )
        self.db.add(task)
        self.db.commit()

        kwargs = {
            'task_uuid': task.uuid,
            'status': 'error',
            'error': 'Cluster deletion fake error'
        }

        receiver.remove_cluster_resp(**kwargs)

        notification = self.db.query(Notification).first()

        self.assertEqual(notification.status, "unread")
        self.assertEqual(notification.topic, "error")
        self.assertEqual(notification.cluster_id, cluster.id)
        self.assertEqual(
            notification.message,
            "Cluster deletion fake error"
        )
