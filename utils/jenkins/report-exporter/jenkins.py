#    Copyright 2014 Mirantis, Inc.
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

import urllib2
import urllib
import urlparse
import json
from settings import JENKINS_HOME


class JSONResource(object):
    def __init__(self, url):
        self.url = url

    def get_data(self):
        try:
            req = urllib2.Request(urlparse.urljoin(self.url, 'api/json'))
            opener = urllib2.build_opener(urllib2.HTTPHandler)
            s = opener.open(req).read()
            return json.loads(s)
        except urllib2.HTTPError:
            return None


class Job(JSONResource):
    def __init__(self, name):
        url = urlparse.urljoin(JENKINS_HOME, 'job/{0}/'.format(urllib.quote(name)))
        super(Job, self).__init__(url)

        self.name = name

    @property
    def builds(self):
        js = self.get_data()
        return [Build(b['number'], b['url']) for b in js['builds']]


class Build(JSONResource):
    def __init__(self, number, url):
        super(Build, self).__init__(url)
        self.number = number

    @property
    def test_report(self):
        return JSONResource(urlparse.urljoin(self.url, 'testReport/')).get_data()
