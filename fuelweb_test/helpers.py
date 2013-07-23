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


import socket
import subprocess
import urllib2
import logging
import json
import threading
import select
from fuelweb_test.integration.decorators import debug


logger = logging.getLogger(__name__)
logwrap = debug(logger)

"""
Integration test helpers
"""


class HTTPClient(object):
    def __init__(self, url=""):
        self.url = url
        self.opener = urllib2.build_opener(urllib2.HTTPHandler)

    def get(self, endpoint):
        req = urllib2.Request(self.url + endpoint)
        return self._open(req)

    def post(self, endpoint, data=None, content_type="application/json"):
        if not data:
            data = {}
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
        return self.opener.open(req)


class LogServer(threading.Thread):
    @logwrap
    def __init__(self, address="localhost", port=5514):
        super(LogServer, self).__init__()
        self.socket = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM
        )
        self.socket.bind((str(address), port))
        self.rlist = [self.socket]
        self._stop = threading.Event()
        self._handler = self.handler
        self._status = False

    def handler(self, messages):
        pass

    def set_status(self, status):
        self._status = status

    def get_status(self):
        return self._status

    def set_handler(self, handler):
        self._handler = handler

    @logwrap
    def stop(self):
        self.socket.close()
        self._stop.set()

    def started(self):
        return not self._stop.is_set()

    def rude_join(self, timeout=None):
        self._stop.set()
        super(LogServer, self).join(timeout)

    def join(self, timeout=None):
        self.rude_join(timeout)

    @logwrap
    def run(self):
        while self.started():
            r, w, e = select.select(self.rlist, [], [], 1)
            if self.socket in r:
                message, addr = self.socket.recvfrom(2048)
                self._handler(message)


class TriggeredLogServer(LogServer):
    def __init__(self, address="localhost", port=5514):
        super(TriggeredLogServer, self).__init__(address, port)
        self.set_handler(self.handler)

    def handler(self, message):
        self.set_status(True)


class Ebtables(object):
    def __init__(self, target_devs, vlans):
        super(Ebtables, self).__init__()
        self.target_devs = target_devs
        self.vlans = vlans

    @logwrap
    def restore_vlans(self):
        for vlan in self.vlans:
            for target_dev in self.target_devs:
                Ebtables.restore_vlan(target_dev, vlan)

    @logwrap
    def restore_first_vlan(self):
        for target_dev in self.target_devs:
            Ebtables.restore_vlan(target_dev, self.vlans[0])

    @logwrap
    def block_first_vlan(self):
        for target_dev in self.target_devs:
            Ebtables.block_vlan(target_dev, self.vlans[0])

    @staticmethod
    @logwrap
    def block_mac(mac):
        return subprocess.check_output(
            ['sudo', 'ebtables', '-t', 'filter', '-A', 'FORWARD', '-s',
             mac, '-j', 'DROP'],
            stderr=subprocess.STDOUT
        )

    @staticmethod
    @logwrap
    def restore_mac(mac):
        return subprocess.call(
            [
                'sudo', 'ebtables', '-t', 'filter',
                '-D', 'FORWARD', '-s', mac, '-j', 'DROP'
            ],
            stderr=subprocess.STDOUT,
        )

    @staticmethod
    @logwrap
    def restore_vlan(target_dev, vlan):
        return subprocess.call(
            ['sudo', 'ebtables', '-t', 'broute', '-D', 'BROUTING', '-i',
             target_dev, '-p', '8021Q', '--vlan-id', str(vlan), '-j', 'DROP'],
            stderr=subprocess.STDOUT,
        )

    @staticmethod
    @logwrap
    def block_vlan(target_dev, vlan):
        return subprocess.check_output(
            ['sudo', 'ebtables', '-t', 'broute', '-A', 'BROUTING', '-i',
             target_dev, '-p', '8021Q', '--vlan-id',  str(vlan), '-j', 'DROP'],
            stderr=subprocess.STDOUT
        )
