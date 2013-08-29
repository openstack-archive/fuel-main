# -*- coding: utf-8 -*-

#    Copyright 2013 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import logging
from logging.handlers import WatchedFileHandler
from StringIO import StringIO

from nailgun.settings import settings

logger = logging.getLogger("nailgun")
api_logger = logging.getLogger("nailgun-api")

SERVER_ERROR_MSG = '500 Internal Server Error'
DATEFORMAT = '%Y-%m-%d %H:%M:%S'
LOGFORMAT = '%(asctime)s %(levelname)s (%(module)s) %(message)s'


class WriteLogger(logging.Logger, object):

    def __init__(self, logger, level=logging.DEBUG):
        super(WriteLogger, self).__init__(logger)
        self.logger = logger

    def write(self, message):
        if message.strip() != '':
            self.logger(message)


class HTTPLoggerMiddleware(object):
    def __init__(self, application):
        self.application = application
        log_file = WatchedFileHandler(settings.API_LOG)
        log_format = logging.Formatter(LOGFORMAT, DATEFORMAT)
        log_file.setFormatter(log_format)
        api_logger.setLevel(logging.DEBUG)
        api_logger.addHandler(log_file)

    def __call__(self, env, start_response):
        env['wsgi.errors'] = WriteLogger(api_logger.error)
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

        if response_code == SERVER_ERROR_MSG:
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
