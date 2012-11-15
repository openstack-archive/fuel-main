# -*- coding: utf-8 -*-

import json
import web

from nailgun.logger import logger
from nailgun.exception import notified
from nailgun.api.models import Notification


class Notifier(object):

    @notified(logger=logger)
    def notify(self, topic, message, cluster_id=None):
        notification = Notification()
        notification.topic = topic
        notification.message = message
        notification.cluster_id = cluster_id
        web.ctx.orm.add(notification)
        web.ctx.orm.commit()
        logger.info("Notification: topic: %s message: %s" % (topic, message))


notifier = Notifier()
