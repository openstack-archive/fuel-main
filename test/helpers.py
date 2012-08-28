import os
import urllib2
import logging
from unittest import TestCase
import paramiko
import posixpath

logger = logging.getLogger('helpers')

"""
Integration test helpers
"""
class HTTPClient(object):
    def __init__(self):
        self.opener = urllib2.build_opener(urllib2.HTTPHandler)

    def get(self, url, log=False):
        req = urllib2.Request(url)
        return self._open(req, log)

    def post(self, url, data="{}", content_type="application/json", log=False):
        req = urllib2.Request(url, data=data)
        req.add_header('Content-Type', content_type)
        return self._open(req, log)

    def put(self, url, data="{}", content_type="application/json", log=False):
        req = urllib2.Request(url, data=data)
        req.add_header('Content-Type', content_type)
        req.get_method = lambda: 'PUT'
        return self._open(req, log)

    def _open(self, req, log):
        try:
            resp = self.opener.open(req)
            content = resp.read()
        except urllib2.HTTPError, error:
            content = ": ".join([str(error.code), error.read()])
        if log:
            logger.debug(content)
        return content


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

    def connect_ssh(self, host, username, password):
        if not self.established:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.host = host
            self.username = username
            self.password = password
            self.ssh_client.connect(host, username=username, password=password)
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
            rel = os.path.relpath(root, frm).replace('\\','/')
            if rel == ".":
                curdir = remote_root
            else:
                curdir =  posixpath.join(remote_root, rel)
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
