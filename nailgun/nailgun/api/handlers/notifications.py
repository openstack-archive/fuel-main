# -*- coding: utf-8 -*-

import json
import logging

import web

from nailgun.api.models import Notification
from nailgun.api.validators import NotificationValidator
from nailgun.api.handlers.base import JSONHandler, content_json


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
    validator = NotificationValidator

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

    @content_json
    def GET(self, notification_id):
        notification = self.get_object_or_404(Notification, notification_id)
        return self.render(notification)

    @content_json
    def PUT(self, notification_id):
        notification = self.get_object_or_404(Notification, notification_id)
        data = self.validator.validate_update(web.data())
        for key, value in data.iteritems():
            setattr(notification, key, value)
        self.db.add(notification)
        self.db.commit()
        return self.render(notification)


class NotificationCollectionHandler(JSONHandler):

    validator = NotificationValidator

    @content_json
    def GET(self):
        user_data = web.input(cluster_id=None)
        query = self.db.query(Notification)
        if user_data.cluster_id:
            query = query.filter_by(cluster_id=user_data.cluster_id)
        # Temporarly limit notifications number to prevent bloating UI by
        # lots of old notifications. Normally, this should be done by querying
        # separately unread notifications for notifier and use pagination for
        # list of all notifications
        query = query.limit(1000)
        notifications = query.all()
        return map(
            NotificationHandler.render,
            notifications
        )

    @content_json
    def PUT(self):
        data = self.validator.validate_collection_update(web.data())
        q = self.db.query(Notification)
        notifications_updated = []
        for nd in data:
            notification = q.get(nd["id"])
            for key, value in nd.iteritems():
                setattr(notification, key, value)
            notifications_updated.append(notification)
            self.db.add(notification)
        self.db.commit()
        return map(
            NotificationHandler.render,
            notifications_updated
        )
