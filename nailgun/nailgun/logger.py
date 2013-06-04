# -*- coding: utf-8 -*-

import sys
import logging
from StringIO import StringIO
from cgitb import html
from logging.handlers import WatchedFileHandler

from nailgun.settings import settings

logger = logging.getLogger("nailgun")
http_logger = logging.getLogger("http")
api_logger = logging.getLogger("nailgun-api")

CATCHID = 'wsgi.catch'
LOGGERID = 'wsgi.errors'
# HTTP error messages
HTTPMSG = '500 Internal Error'
ERRORMSG = 'Server got itself in trouble'
# Default log formats
DATEFORMAT = '%d-%m-%Y %H:%M:%S'
LOGFORMAT = '%(asctime)s %(levelname)s (%(module)s) %(message)s'
HTTP_LOGFORMAT = '%(message)s'


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


class HTTPLoggerMiddleware(object):
    def __init__(self, application, **kw):
        self.application = application
        log_file = WatchedFileHandler(kw.get('file', settings.API_LOG))
        log_format = logging.Formatter(
            kw.get('logformat', LOGFORMAT),
            kw.get('datefmt', DATEFORMAT))
        log_file.setFormatter(log_format)
        api_logger.setLevel(kw.get('loglevel', logging.DEBUG))
        api_logger.addHandler(log_file)

    def __call__(self, env, start_response):
        self.__logging_request(env)

        def start_response_with_logging(status, headers, *args):
            self.__logging_response(env, status)
            return start_response(status, headers, *args)

        return self.application(env, start_response_with_logging)

    def __logging_response(self, env, response_code):
        response_info = "Response code '%s' for %s %s from %s:%s" % (
            response_code,
            env['REQUEST_METHOD'],
            env['REQUEST_URI'],
            self.__get_remote_ip(env),
            env['REMOTE_PORT'],
        )

        if response_code == '500 Internal Server Error':
            api_logger.error(response_info)
        else:
            api_logger.debug(response_info)

    def __logging_request(self, env):
        length = int(env.get('CONTENT_LENGTH', 0))
        body = ''

        if length != 0:
            body = env['wsgi.input'].read(length)
            env['wsgi.input'] = StringIO(body)

        request_info = "Request %s %s from %s:%s %s" % (
            env['REQUEST_METHOD'],
            env['REQUEST_URI'],
            self.__get_remote_ip(env),
            env['REMOTE_PORT'],
            body
        )

        api_logger.debug(request_info)

    def __get_remote_ip(self, env):
        if 'HTTP_X_REAL_IP' in env:
            return env['HTTP_X_REAL_IP']
        elif 'REMOTE_ADDR' in env:
            return env['REMOTE_ADDR']
        else:
            return 'can not determine ip'


class FileLoggerMiddleware(object):

    def __init__(self, application, **kw):
        self.application = application
        self._errapp = kw.get('errapp', _errapp)
        self.log = kw.get('log', True)
        if self.log:
            self.message = kw.get('logmessage', ERRORMSG)
            logger = http_logger
            logger.setLevel(kw.get('loglevel', logging.DEBUG))
            log_format = logging.Formatter(
                kw.get('logformat', HTTP_LOGFORMAT),
                kw.get('datefmt', DATEFORMAT))
            filelogger = WatchedFileHandler(kw.get('file',
                                            settings.ACCESS_LOG))
            filelogger.setFormatter(log_format)
            logger.addHandler(filelogger)
            self.logger = WriteLogger(logger)
            self.nailgun_logger = logging.getLogger("nailgun")

    def __call__(self, env, start_response):
        if self.log:
            env[LOGGERID] = self.logger
        env[CATCHID] = self.catch
        try:
            return self.application(env, start_response)
        except:
            return self.catch(env, start_response)

    def catch(self, env, start_response):
        '''
        Exception catcher.
        All exceptions should be in nailgun log
        '''
        # Log exception
        if self.log:
            self.nailgun_logger.exception(self.message)
        # Return error handler
        return self._errapp(env, start_response)
