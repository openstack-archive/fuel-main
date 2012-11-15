# -*- coding: utf-8 -*-

import json
import web

from nailgun.logger import logger
from nailgun.exception import notified
from nailgun.api.models import Notification


class DbNotifier(object):

    @classmethod
    @notified(level=10, logger=logger)
    def notify(cls, level, payload):
        try:
            logger.debug("Trying to treat notification message as json")
            message = json.loads(payload)
        except:
            logger.debug("Notification message seems it's not a valid json")
            message = payload

        notification = Notification()
        notification.level = level
        if isinstance(message, dict):
            notification.message = message['message']
            notification.cluster_id = message.get('cluster', None)
        else:
            notification.message = message
            notification.cluster_id = None
        web.ctx.orm.add(notification)
        web.ctx.orm.commit()


class Notifier(object):
    driver = DbNotifier

    def __init__(self, driver=None):
        if driver:
            self.driver = driver

    def notify(self, level, message):
        self.driver.notify(level, message)

    def debug(self, message):
        self.notify(10, message)

    def info(self, message):
        self.notify(20, message)

    def warn(self, message):
        self.notify(30, message)

    def error(self, message):
        self.notify(40, message)

    def critical(self, message):
        self.notify(50, message)


notifier = Notifier()
