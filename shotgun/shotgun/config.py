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

import time

from shotgun import settings


class Config(object):
    def __init__(self, data=None):
        self.data = data
        self.time = time.localtime()

    def _timestamp(self, name):
        return "{0}-{1}".format(
            name,
            time.strftime('%Y-%m-%d_%H-%M-%S', self.time)
        )

    @property
    def target(self):
        target = self.data.get("target", settings.TARGET)
        if self.data.get("timestamp", settings.TIMESTAMP):
            target = self._timestamp(target)
        return target

    @property
    def lastdump(self):
        return self.data.get("lastdump", settings.LASTDUMP)

    @property
    def objects(self):
        for role, hosts in self.data["dump_roles"].iteritems():
            for host in hosts:
                for obj in self.data["dump_objects"].get(role, []):
                    obj["host"] = host
                    yield obj
