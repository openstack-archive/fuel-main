# -*- coding: utf-8 -*-

from settings import settings
from wsgilog import WsgiLog


class Log(WsgiLog):
    def __init__(self, application):
        WsgiLog.__init__(
            self,
            application,
            logformat='%(message)s',
            tofile=False,
            toprint=True,
            #file=settings.LOGFILE
        )
