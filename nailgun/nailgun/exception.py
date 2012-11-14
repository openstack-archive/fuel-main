# -*- coding: utf-8 -*-

import logging
import functools

from nailgun.logger import logger


def notified(level=10, logger=None, notifier=None, avoid=True):
    """
    Decorate your methods to catch thrown exceptions and log them.

    Usage:

    @notified([level][, notifier][, logger][, avoid])
    def method(argument):
        raise Exception("test exception")
    """

    def wrapper(func):
        def caller(*args, **kw):
            try:
                return func(*args, **kw)
            except Exception, e:
                p = dict(func=func.__name__, args=args, exception=e)
                p.update(kw)
                exception_message = str(p)

                if not notifier is None:
                    notifier.notify(level, exception_message)

                if not logger is None:
                    logger.log(level, exception_message)

                if not avoid:
                    raise e

        return functools.wraps(func)(caller)
    return wrapper


class NailgunBaseException(Exception):
    """Base Nailgun Exception"""

    message = "An unknown exception occurred."
    level = 10
    logger = None
    notifier = None

    def __init__(self, message=None, logger=None, notifier=None):

        if message is None:
            message = self.message

        if not logger is None:
            self.logger = logger

        if not notifier is None:
            self.notifier = notifier

        self._realize(message)
        super(BaseException, self).__init__(message)

    def _realize(self, message):
        if not self.logger is None:
            self.logger.log(self.level, message)
        if not self.notifier is None:
            self.notifier.notify(self.level, message)
