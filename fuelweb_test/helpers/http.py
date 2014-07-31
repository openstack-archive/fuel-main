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

import json
import urllib2

from keystoneclient.v2_0 import Client as keystoneclient
from keystoneclient import exceptions
from fuelweb_test import logger


class HTTPClient(object):

    def __init__(self, url, keystone_url, credentials, **kwargs):
        logger.info('Initiate HTTPClient with url %s', url)
        self.url = url
        self.keystone_url = keystone_url
        self.creds = dict(credentials, **kwargs)
        self.token = None
        self.authenticate()
        self.opener = urllib2.build_opener(urllib2.HTTPHandler)

    def authenticate(self):
        try:
            logger.info('Initialize keystoneclient with url %s',
                        self.keystone_url)
            self.keystone = keystoneclient(
                auth_url=self.keystone_url, **self.creds)
            # it depends on keystone version, some versions doing auth
            # explicitly some dont, but we are making it explicitly always
            self.keystone.authenticate()
            self.token = self.keystone.auth_token
            logger.debug('Authorization token is successfully updated')
        except exceptions.AuthorizationFailure:
            logger.warning(
                'Cant establish connection to keystone with url %s',
                self.keystone_url)
            self.token = None

    def get(self, endpoint):
        req = urllib2.Request(self.url + endpoint)
        return self._open(req)

    def post(self, endpoint, data=None, content_type="application/json"):
        if not data:
            data = {}
        logger.info('self url is %s' % self.url)
        req = urllib2.Request(self.url + endpoint, data=json.dumps(data))
        req.add_header('Content-Type', content_type)
        return self._open(req)

    def put(self, endpoint, data=None, content_type="application/json"):
        if not data:
            data = {}
        req = urllib2.Request(self.url + endpoint, data=json.dumps(data))
        req.add_header('Content-Type', content_type)
        req.get_method = lambda: 'PUT'
        return self._open(req)

    def delete(self, endpoint):
        req = urllib2.Request(self.url + endpoint)
        req.get_method = lambda: 'DELETE'
        return self._open(req)

    def _open(self, req):
        if self.token is not None:
            logger.debug('Set X-Auth-Token to %s', self.token)
            req.add_header("X-Auth-Token", self.token)
        try:
            response = self.opener.open(req)
        except urllib2.HTTPError as e:
            if e.code == 401:
                logger.warning('Authorization failure: '.format(e))
                logger.debug('')
                self.authenticate()
                response = self.opener.open(req)
            else:
                raise
        return response
