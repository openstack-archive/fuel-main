import os
import urllib2
import logging
from unittest import TestCase
import paramiko

logging.basicConfig(format=':%(lineno)d: %(asctime)s %(message)s', level=logging.DEBUG)


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
            content = error.read()
        if log:
            logging.debug(content)
        return content


class SSHClient(object):

    def __init__(self):
        self.channel = None
        self.sudo = False

    def connect_ssh(self, host, username, password):
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.host = host
        self.username = username
        self.password = password
        self.ssh_client.connect(host, username=username, password=password)
        self.sftp_client = self.ssh_client.open_sftp()

    def open_channel(self):
        if not self.channel:
            self.channel = self.ssh_client.invoke_shell()

    def aquire_sudo(self):
        if not self.channel:
            self.open_channel()
        if not self.sudo:
            logging.info("Aquiring sudo")
            self.channel.send("sudo -s\n")
            self._recv_until("%s: " % self.username)
            self.channel.send("%s\n" % self.password)
            self._recv_until("# ")
            self.sudo = True

    def exec_cmd(self, command, sudo=False):
        logging.info("Executing command: '%s'" % command)
        if not self.channel:
            self.open_channel()
        if sudo and not self.sudo:
            self.aquire_sudo()
        self.channel.send("%s\n" % command)
        if sudo or self.sudo:
            return self._recv_until("# ")
        else:
            return self._recv_until("$ ")

    def mkdir(self, path, sudo=False):
        logging.info("Creating directory: %s" % path)
        if not sudo:
            self.sftp_client.mkdir(path)
        else:
            self.open_channel()
            self.aquire_sudo()
            self.channel.send("mkdir %s\n" % path)
            self._recv_until("# ")


    def rmdir(self, path, sudo=False):
        logging.info("Removing directory: %s" % path)
        if not sudo:
            self.ssh_client.exec_command("rm -rf %s" % path)
        else:
            self.open_channel()
            self.aquire_sudo()
            self.channel.send("rm -rf %s\n" % path)
            self._recv_until("# ")

    def scp(self, frm, to):
        logging.info("Copying file: %s -> %s" % (frm, to))
        self.sftp_client.put(frm, to)

    def scp_d(self, frm, to):
        logging.info("Copying directory: %s -> %s" % (frm, to))
        remote_root = os.path.join(
            to,
            os.path.basename(frm)
        )
        for root, dirs, fls in os.walk(frm):
            rel = os.path.relpath(root, frm)
            if rel == ".":
                curdir = remote_root
            else:
                curdir = os.path.join(remote_root, rel)
            self.sftp_client.mkdir(curdir)
            for fl in fls:
                self.sftp_client.put(
                    os.path.join(root, fl),
                    os.path.join(curdir, fl)
                )

    def disconnect(self):
        self.sftp_client.close()
        self.ssh_client.close()

    def _recv_until(self, data):
        buff = ""
        while not buff.endswith(data):
            resp = self.channel.recv(9999)
            buff += resp
        return buff
