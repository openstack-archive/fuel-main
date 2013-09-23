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

"""
Handlers dealing with notifications
"""

import json
import logging

import web

from nailgun.db import db
from nailgun.api.models import Notification
from nailgun.api.validators.notification import NotificationValidator
from nailgun.api.handlers.base import JSONHandler, content_json
from nailgun.settings import settings


class NotificationHandler(JSONHandler):
    """
    Notification single handler
    """

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
        """
        :returns: JSONized Notification object.
        :http: * 200 (OK)
               * 404 (notification not found in db)
        """
        notification = self.get_object_or_404(Notification, notification_id)
        return self.render(notification)

    @content_json
    def PUT(self, notification_id):
        """
        :returns: JSONized Notification object.
        :http: * 200 (OK)
               * 400 (invalid notification data specified)
               * 404 (notification not found in db)
        """
        notification = self.get_object_or_404(Notification, notification_id)
        data = self.validator.validate_update(web.data())
        for key, value in data.iteritems():
            setattr(notification, key, value)
        db().add(notification)
        db().commit()
        return self.render(notification)


class NotificationCollectionHandler(JSONHandler):

    validator = NotificationValidator

    @content_json
    def GET(self):
        """
        :returns: Collection of JSONized Notification objects.
        :http: * 200 (OK)
        """
        user_data = web.input(limit=settings.MAX_ITEMS_PER_PAGE)
        limit = user_data.limit
        query = db().query(Notification).limit(limit)
        notifications = query.all()
        return map(
            NotificationHandler.render,
            notifications
        )

    @content_json
    def PUT(self):
        """
        :returns: Collection of JSONized Notification objects.
        :http: * 200 (OK)
               * 400 (invalid data specified for collection update)
        """
        data = self.validator.validate_collection_update(web.data())
        q = db().query(Notification)
        notifications_updated = []
        for nd in data:
            notification = q.get(nd["id"])
            for key, value in nd.iteritems():
                setattr(notification, key, value)
            notifications_updated.append(notification)
            db().add(notification)
        db().commit()
        return map(
            NotificationHandler.render,
            notifications_updated
        )
