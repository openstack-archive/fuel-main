# -*- coding: utf-8 -*-

import json
import logging

import web

from nailgun.db import orm
from nailgun.api.models import Notification
from nailgun.api.handlers.base import JSONHandler


class NotificationHandler(JSONHandler):
    fields = (
        "id",
        "cluster",
        "topic",
        "message",
        "status",
        "node_id",
        "task_id"
    )
    model = Notification

    @classmethod
    def render(cls, instance, fields=None):
        json_data = JSONHandler.render(instance, fields=cls.fields)
        json_data["time"] = ":".join([
            instance.datetime.strftime("%H"),
            instance.datetime.strftime("%M"),
            instance.datetime.strftime("%S")
        ])
        json_data["date"] = "-".join([
            instance.datetime.strftime("%d"),
            instance.datetime.strftime("%m"),
            instance.datetime.strftime("%Y")
        ])
        return json_data

    def GET(self, notification_id):
        web.header('Content-Type', 'application/json')
        notification = orm().query(Notification).get(notification_id)
        if not notification:
            return web.notfound()
        return json.dumps(
            self.render(notification),
            indent=4
        )

    def PUT(self, notification_id):
        web.header('Content-Type', 'application/json')
        notification = orm().query(Notification).get(notification_id)
        if not notification:
            return web.notfound()
        data = Notification.validate_update(web.data())
        for key, value in data.iteritems():
            setattr(notification, key, value)
        orm().add(notification)
        orm().commit()
        return json.dumps(
            self.render(notification),
            indent=4
        )


class NotificationCollectionHandler(JSONHandler):

    def GET(self):
        web.header('Content-Type', 'application/json')
        user_data = web.input(cluster_id=None)
        query = orm().query(Notification)
        if user_data.cluster_id:
            query = query.filter_by(cluster_id=user_data.cluster_id)
        # Temporarly limit notifications number to prevent bloating UI by
        # lots of old notifications. Normally, this should be done by querying
        # separately unread notifications for notifier and use pagination for
        # list of all notifications
        query = query.limit(1000)
        notifications = query.all()
        return json.dumps(map(
            NotificationHandler.render,
            notifications), indent=4)

    def PUT(self):
        web.header('Content-Type', 'application/json')
        data = Notification.validate_collection_update(web.data())
        q = orm().query(Notification)
        notifications_updated = []
        for nd in data:
            notification = q.get(nd["id"])
            for key, value in nd.iteritems():
                setattr(notification, key, value)
            notifications_updated.append(notification)
            orm().add(notification)
        orm().commit()
        return json.dumps(map(
            NotificationHandler.render,
            notifications_updated), indent=4)
