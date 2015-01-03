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
import socket
import daemon
try:
    from daemon.pidlockfile import PIDLockFile
except ImportError:
    from lockfile.pidlockfile import PIDLockFile
from lockfile import LockTimeout
from signal import SIGTERM
import BaseHTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler

class SimpleHTTPDaemon:
    def __init__(self, address='0.0.0.0', port='9001',
                 pid_file='/var/run/simplehttpd.pid'):
        self.address = address
        self.port = port
        self.pid = PIDLockFile(pid_file)
        if self.pid.read_pid() != None and os.getpid() != self.pid.read_pid():
            try:
                os.kill(self.pid.read_pid(), 0)
                print 'Process already running!'
                sys.exit(1)
            except OSError:
                self.pid.break_lock()

    def run_http_server(self):
        HandlerClass = SimpleHTTPRequestHandler
        ServerClass = BaseHTTPServer.HTTPServer
        Protocol = "HTTP/1.0"
        server_address = (self.address, self.port)
        HandlerClass.protocol_version = Protocol
        self.httpd = ServerClass(server_address, HandlerClass)
        self.httpd.serve_forever()

    def start(self):
        context = daemon.DaemonContext(
                pidfile=self.pid,
                working_directory=os.getcwd(),
                signal_map={
                    SIGTERM: self.stop
                }
            )
        with context:
            self.run_http_server()

    def stop(self):
        self.httpd.shutdown()
        self.pid.release()
        sys.exit(0)

if __name__ == "__main__":

    if sys.argv[1:]:
        port = int(sys.argv[1])
    else:
        port = 9001

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1',port))
    if result == 0:
        print 'Port already opened'
        sys.exit(1)

    if sys.argv[2:]:
        pid = sys.argv[2]
    else:
        pid = '/var/run/simplehttpd.pid'

    server = SimpleHTTPDaemon('0.0.0.0', port, pid)
    server.start()
