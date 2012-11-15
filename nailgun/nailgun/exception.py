# -*- coding: utf-8 -*-

import sys
import traceback
import logging
import functools

from nailgun.logger import logger


def notified(logger=None, avoid_raising=False):
    """
    Decorate your methods to catch thrown exceptions and log them.

    Usage:

    @notified([level][, logger][, avoid_raising])
    def method(argument):
        raise Exception("test exception")
    """

    def wrapper(func):
        def caller(*args, **kw):
            try:
                return func(*args, **kw)
            except Exception as e:
                debug_data = dict(func=func.__name__, args=args)
                debug_data.update(kw)
                logger.debug("Exception has been caught in "
                             "notified decorator:\n%s" %
                             str(debug_data))

                exception_trace = traceback.format_exception(*sys.exc_info())
                logger.debug("Exception trace:\n%s" %
                             "\n".join(exception_trace))

                if not avoid_raising:
                    raise e

        return functools.wraps(func)(caller)
    return wrapper


class ParentException(Exception):
    """Parent Exception"""

    topic = "Undefined topic"
    message = "An unknown exception occurred."

    def __init__(self, message=None, topic=None, cluster_id=None,
                 level=10, logger=None, notifier=None):

        if message:
            self.message = message

        if topic:
            self.topic = topic

        self.cluster_id = cluster_id
        self.logger = logger
        self.notifier = notifier
        self.level = level

        if self.logger:
            self.logger.log(self.level, self.message)

        if self.notifier:
            self.notifier.notify(self.topic, self.message, self.cluster_id)

        super(ParentException, self).__init__(self.message)

