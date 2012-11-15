# -*- coding: utf-8 -*-

import json
import logging

import web

from nailgun.api.models import Notification
from nailgun.api.handlers.base import JSONHandler


class NotificationHandler(JSONHandler):
    fields = (
        "id",
        "cluster",
        "level",
        "message",
        "status",
    )
    model = Notification

    def GET(self, notification_id):
        web.header('Content-Type', 'application/json')
        q = web.ctx.orm.query(Notification)
        notification = q.filter(Notification.id == notification_id).first()
        if not notification:
            return web.notfound()
        return json.dumps(
            self.render(notification),
            indent=4
        )

    def PUT(self, notification_id):
        web.header('Content-Type', 'application/json')
        notification = web.ctx.orm.query(Notification).get(notification_id)
        if not notification:
            return web.notfound()
        data = Notification.validate_update(web.data())
        for key, value in data.iteritems():
            setattr(notification, key, value)
        web.ctx.orm.add(notification)
        web.ctx.orm.commit()
        return json.dumps(
            self.render(notification),
            indent=4
        )


class NotificationCollectionHandler(JSONHandler):

    def GET(self):
        web.header('Content-Type', 'application/json')
        user_data = web.input(cluster_id=None)
        if user_data.cluster_id:
            notifications = web.ctx.orm.query(Notification).filter_by(
                cluster_id=user_data.cluster_id).all()
        else:
            notifications = web.ctx.orm.query(Notification).all()
        return json.dumps(map(
            NotificationHandler.render,
            notifications), indent=4)

    def PUT(self):
        web.header('Content-Type', 'application/json')
        data = Notification.validate_collection_update(web.data())
        q = web.ctx.orm.query(Notification)
        notifications_updated = []
        for nd in data:
            notification = q.get(nd["id"])
            for key, value in nd.iteritems():
                setattr(notification, key, value)
            notifications_updated.append(notification)
            web.ctx.orm.add(notification)
        web.ctx.orm.commit()
        return json.dumps(map(
            NotificationHandler.render,
            notifications_updated), indent=4)
