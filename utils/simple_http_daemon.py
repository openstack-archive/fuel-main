#!/usr/bin/env python
#
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

import sys
import os
import time
import daemon
import daemon.pidlockfile
import BaseHTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler

class SimpleHTTPDaemon:
    def __init__(self, address='0.0.0.0', port='9001', pid_file='/var/run/simplehttpd.pid', ttl=600):
        self.address = address
        self.port = port
        self.pid_file = pid_file
        self.ttl = ttl
        self.end = 0

    def run_http_server(self):
        HandlerClass = SimpleHTTPRequestHandler
        ServerClass  = BaseHTTPServer.HTTPServer
        Protocol     = "HTTP/1.0"
        server_address = (self.address, self.port)
        HandlerClass.protocol_version = Protocol
        httpd = ServerClass(server_address, HandlerClass)
        while time.time() < self.end:
            httpd.handle_request()

    def start(self):
        self.end = time.time() + self.ttl
        context = daemon.DaemonContext(
            working_directory = os.getcwd(),
            umask = 0o002,
            pidfile = daemon.pidlockfile.PIDLockFile(self.pid_file),
            )
        with context:
            self.run_http_server()

if __name__ == "__main__":

    if sys.argv[1:]:
        port = int(sys.argv[1])
    else:
        port = 9001

    if sys.argv[2:]:
        pid = sys.argv[2]
    else:
        pid = '/var/run/simplehttpd.pid'

    server = SimpleHTTPDaemon('0.0.0.0', port, pid, 600)
    server.start()

