import os
import urllib2
import logging
import posixpath
import json
import socket
import threading
import sys
import select
import time

import paramiko

logger = logging.getLogger(__name__)

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

    def post(self, endpoint, data={}, content_type="application/json"):
        req = urllib2.Request(self.url + endpoint, data=json.dumps(data))
        req.add_header('Content-Type', content_type)
        return self._open(req)

    def put(self, endpoint, data={}, content_type="application/json"):
        req = urllib2.Request(self.url + endpoint, data=json.dumps(data))
        req.add_header('Content-Type', content_type)
        req.get_method = lambda: 'PUT'
        return self._open(req)

    def _open(self, req):
        try:
            res = self.opener.open(req)
        except urllib2.HTTPError as err:
            res = type(
                'HTTPError',
                (object,),
                {
                    'read': lambda s: str(err),
                    'getcode': lambda s: err.code
                }
            )()
        return res


class SSHClient(object):
    class get_sudo(object):
        def __init__(self, client):
            self.client = client

        def __enter__(self):
            self.client.sudo_mode = True

        def __exit__(self, type, value, traceback):
            self.client.sudo_mode = False

    def __init__(self):
        self.channel = None
        self.sudo_mode = False
        self.sudo = self.get_sudo(self)
        self.established = False

    def connect_ssh(self, host, username=None, password=None,
                    key_filename=None):
        if not self.established:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(
                paramiko.AutoAddPolicy()
            )
            self.host = host
            self.username = username
            self.password = password
            self.key_filename = key_filename
            self.ssh_client.connect(host, username=username, password=password,
                                    key_filename=key_filename)
            self.sftp_client = self.ssh_client.open_sftp()
            self.established = True

    def execute(self, command):
        logger.debug("Executing command: '%s'" % command.rstrip())
        chan = self.ssh_client.get_transport().open_session()
        stdin = chan.makefile('wb')
        stdout = chan.makefile('rb')
        stderr = chan.makefile_stderr('rb')
        cmd = "%s\n" % command
        if self.sudo_mode:
            cmd = 'sudo -S bash -c "%s"' % cmd.replace('"', '\\"')
        chan.exec_command(cmd)
        if stdout.channel.closed is False:
            stdin.write('%s\n' % self.password)
            stdin.flush()
        result = {
            'stdout': [],
            'stderr': [],
            'exit_status': chan.recv_exit_status()
        }
        for line in stdout:
            result['stdout'].append(line)
        for line in stderr:
            result['stderr'].append(line)

        return result

    def mkdir(self, path):
        logger.debug("Creating directory: %s" % path)
        return self.execute("mkdir %s\n" % path)

    def rmdir(self, path):
        logger.debug("Removing directory: %s" % path)
        return self.execute("rm -rf %s" % path)

    def open(self, path, mode='r'):
        return self.sftp_client.open(path, mode)

    def scp(self, frm, to):
        logger.debug("Copying file: %s -> %s" % (frm, to))
        self.sftp_client.put(frm, to)

    def scp_d(self, frm, to):
        logger.debug("Copying directory: %s -> %s" % (frm, to))
        remote_root = posixpath.join(
            to,
            os.path.basename(frm)
        )
        for root, dirs, fls in os.walk(frm):
            rel = os.path.relpath(root, frm).replace('\\', '/')
            if rel == ".":
                curdir = remote_root
            else:
                curdir = posixpath.join(remote_root, rel)
            self.mkdir(curdir)
            for fl in fls:
                self.scp(
                    os.path.join(root, fl),
                    posixpath.join(curdir, fl)
                )

    def disconnect(self):
        self.sftp_client.close()
        self.ssh_client.close()
        self.established = False


class LogServer(threading.Thread):
    def __init__(self, address="localhost", port=5514):
        logger.debug("Initializing LogServer: %s:%s",
                     str(address), str(port))
        super(LogServer, self).__init__()
        self.socket = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM
        )
        self.socket.bind((str(address), port))
        self.rlist = [self.socket]
        self._stop = threading.Event()
        self._handler = self.default_handler

    @classmethod
    def default_handler(cls, message):
        pass

    def set_handler(self, handler):
        self._handler = handler

    def stop(self):
        logger.debug("LogServer is stopping ...")
        self.socket.close()
        self._stop.set()

    def rude_join(self, timeout=None):
        self._stop.set()
        super(LogServer, self).join(timeout)

    def join(self, timeout=None):
        self.rude_join(timeout)

    def run(self):
        logger.debug("LogServer is listening for messages ...")
        while not self._stop.is_set():
            r, w, e = select.select(self.rlist, [], [], 1)
            if self.socket in r:
                message, addr = self.socket.recvfrom(2048)
                self._handler(message)

