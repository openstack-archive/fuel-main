# -*- coding: utf-8 -*-

from nailgun.logger import logger


class NailgunException(Exception):

    def __init__(self, message, log_traceback=False):
        self.log_traceback = log_traceback
        self.message = message
        super(NailgunException, self).__init__()

    def __str__(self):
        return self.message
