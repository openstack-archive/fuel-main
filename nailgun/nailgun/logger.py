# -*- coding: utf-8 -*-

import sys
import logging
from cgitb import html
from logging.handlers import HTTPHandler, SysLogHandler
from logging.handlers import TimedRotatingFileHandler, SMTPHandler

from nailgun.settings import settings

logger = logging.getLogger("nailgun")

CATCHID = 'wsgi.catch'
LOGGERID = 'wsgi.errors'
# HTTP error messages
HTTPMSG = '500 Internal Error'
ERRORMSG = 'Server got itself in trouble'
# Default log formats
DATEFORMAT = '%d-%m-%Y %H:%M:%S'
LOGFORMAT = '%(message)s'


def _errapp(environ, start_response):
    '''Default error handling WSGI application.'''
    start_response(HTTPMSG, [('Content-type', 'text/plain')], sys.exc_info())
    return [ERRORMSG]


class WriteLogger(logging.Logger, object):

    def __init__(self, logger, level=logging.DEBUG):
        # Set logger level
        logger.propagate = False
        super(WriteLogger, self).__init__(logger)
        if level == logging.DEBUG:
            self.logger = logger.debug
        elif level == logging.CRITICAL:
            self.logger = logger.critical
        elif level == logging.ERROR:
            self.logger = logger.warning
        elif level == logging.WARNING:
            self.logger = logger.warning
        elif level == logging.INFO:
            self.logger = logger.info

    def write(self, info):
        if info.lstrip().rstrip() != '':
            self.logger(info)


class FileLoggerMiddleware(object):

    def __init__(self, application, **kw):
        self.application = application
        self._errapp = kw.get('errapp', _errapp)
        self.log = kw.get('log', True)
        if self.log:
            self.message = kw.get('logmessage', ERRORMSG)
            logger = logging.getLogger(
                kw.get('logname', 'nailgun')
            )
            logger.setLevel(
                kw.get('loglevel', logging.DEBUG)
            )
            format = logging.Formatter(
                kw.get('logformat', LOGFORMAT),
                kw.get('datefmt', DATEFORMAT)
            )
            filelogger = TimedRotatingFileHandler(
                kw.get('file', settings.ACCESS_LOG),
                kw.get('interval', 'h'),
                kw.get('backups', 1)
            )
            filelogger.setFormatter(format)
            logger.addHandler(filelogger)
            self.logger = WriteLogger(logger)

    def __call__(self, environ, start_response):
        if self.log:
            environ[LOGGERID] = self.logger
        environ[CATCHID] = self.catch
        try:
            return self.application(environ, start_response)
        except:
            return self.catch(environ, start_response)

    def catch(self, environ, start_response):
        '''Exception catcher.'''
        # Log exception
        if self.log:
            self.logger.exception(self.message)
        # Return error handler
        return self._errapp(environ, start_response)
