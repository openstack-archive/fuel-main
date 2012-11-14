# -*- coding: utf-8 -*-

import web

from nailgun.logger import logger
from nailgun.api.models import Notification
from nailgun.exception import NailgunBaseException


class NotifierException(NailgunBaseException):
    level = 40
    logger = logger
    notifier = None


class DbNotifier(object):

    @classmethod
    def notify(cls, message, level, **kwargs):
        try:
            notification = Notification()
            notification.level = level
            notification.message = message
            for k, v in kwargs.iteritems():
                setattr(notification, k, v)
            web.ctx.orm.add(notification)
            web.ctx.orm.commit()

        except Exception as e:
            raise NotifierException("Error while writing notification "
                                    "into database: %s" % str(e))


class Notifier(object):
    driver = DbNotifier

    def __init__(self, driver=None):
        if not driver is None:
            self.driver = driver

    def notify(self, *args, **kwargs):
        self.driver.notify(*args, **kwargs)


notifier = Notifier()
