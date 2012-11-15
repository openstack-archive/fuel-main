# -*- coding: utf-8 -*-

import logging
import functools

from nailgun.logger import logger


def notified(level=10, logger=None, notifier=None, avoid_raising=False):
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
                debug_data = dict(func=func.__name__, args=args, exception=e)
                debug_data.update(kw)
                logger.debug("Exception caught in notified decorator:\n%s" %
                             str(debug_data))

                exception_message = getattr(e, 'message', str(e))

                if not notifier is None:
                    notifier.notify(level, exception_message)

                if not logger is None:
                    logger.log(level, exception_message)

                if not avoid_raising:
                    raise e

        return functools.wraps(func)(caller)
    return wrapper


class ParentException(Exception):
    """Parent Exception"""

    message = "An unknown exception occurred."

    def __init__(self, message=None, level=10, logger=None, notifier=None):

        if message is None:
            message = self.message

        self.logger = logger
        self.notifier = notifier
        self.level = level

        self._note(message)
        super(ParentException, self).__init__(message)

    def _note(self, message):
        if not self.logger is None:
            self.logger.log(self.level, message)
        if not self.notifier is None:
            self.notifier.notify(self.level, message)
