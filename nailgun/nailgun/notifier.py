# -*- coding: utf-8 -*-

import json
import web

from nailgun.logger import logger
from nailgun.api.models import Notification


class Notifier(object):

    def notify(self, topic, message, cluster_id=None, db=None):
        if not db:
            db = web.ctx.orm
        notification = Notification()
        notification.topic = topic
        notification.message = message
        notification.cluster_id = cluster_id
        db.add(notification)
        db.commit()
        logger.info("Notification: topic: %s message: %s" % (topic, message))


notifier = Notifier()
