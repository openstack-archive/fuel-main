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

import select
import socket
import threading

from fuelweb_test import logwrap


class LogServer(threading.Thread):
    """LogServer."""  # TODO documentation

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
    """TriggeredLogServer."""  # TODO documentation

    def __init__(self, address="localhost", port=5514):
        super(TriggeredLogServer, self).__init__(address, port)
        self.set_handler(self.handler)

    def handler(self, message):
        self.set_status(True)
