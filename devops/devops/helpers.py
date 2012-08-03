import os
import stat
import socket
import time
import httplib
import xmlrpclib
import paramiko
import string

import logging
logger = logging.getLogger('devops.helpers')

class TimeoutError(Exception): pass
class AuthenticationError(Exception): pass

def icmp_ping(host, timeout=1):
    "icmp_ping(host, timeout=1) - returns True if host is pingable; False - otherwise."
    return os.system("ping -c 1 -W '%(timeout)d' '%(host)s' 1>/dev/null 2>&1" % { 'host': str(host), 'timeout': timeout}) == 0

def tcp_ping(host, port):
    "tcp_ping(host, port) - returns True if TCP connection to specified host and port can be established; False - otherwise."
    s = socket.socket()
    try:
        s.connect((str(host), int(port)))
    except socket.error:
        return False
    s.close()
    return True

def wait(predicate, interval=5, timeout=None):
    """
      wait(predicate, interval=5, timeout=None) - wait until predicate will become True. Returns number of seconds that is left or 0 if timeout is None.
      Options:
        interval - seconds between checks.
        timeout  - raise TimeoutError if predicate won't become True after this amount of seconds. 'None' disables timeout.
    """
    start_time = time.time()
    while not predicate():
        if timeout and start_time + timeout < time.time():
            raise TimeoutError, "Waiting timed out"

        seconds_to_sleep = interval
        if timeout:
            seconds_to_sleep = max(0, min(seconds_to_sleep, start_time + timeout - time.time()))
        time.sleep(seconds_to_sleep)

    return timeout + start_time - time.time() if timeout else 0

def http(host='localhost', port=80, method='GET', url='/', waited_code=200):
    try:
        conn = httplib.HTTPConnection(str(host), int(port))
        conn.request(method, url)
        res = conn.getresponse()
        
        if res.status == waited_code:
            return True
        return False
    except:
        return False


class KeyPolicy(paramiko.WarningPolicy):
    def missing_host_key(self, client, hostname, key):
        return
    
class SSHClient(object):
    class get_sudo(object):
        def __init__(self, ssh):
            self.ssh = ssh

        def __enter__(self):
            self.ssh.sudo_mode = True

        def __exit__(self, type, value, traceback):
            self.ssh.sudo_mode = False

    def __init__(self, host, port=22, username=None, password=None):
        self.host = str(host)
        self.port = int(port)
        self.username = username
        self.password = password

        self.sudo_mode = False
        self.sudo = self.get_sudo(self)

        self.reconnect()

    def __del__(self):
        self.sftp.close()
        self.ssh.close()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        pass

    def reconnect(self):
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(self.host, port=self.port, username=self.username, password=self.password)
        self.sftp = self.ssh.open_sftp()

    def execute(self, command):
        logger.debug("Executing command: '%s'" % command.rstrip())
        chan = self.ssh.get_transport().open_session()
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
            'exit_code': chan.recv_exit_status()
        }
        for line in stdout:
            result['stdout'].append(line)
        for line in stderr:
            result['stderr'].append(line)

        return result

    def mkdir(self, path):
        logger.debug("Creating directory: %s" % path)
        return self.execute("mkdir %s\n" % path)

    def rm_rf(self, path):
        logger.debug("Removing directory: %s" % path)
        return self.execute("rm -rf %s" % path)

    def open(self, path, mode='r'):
        return self.sftp.open(path, mode)

    def upload(self, source, target):
        logger.debug("Copying '%s' -> '%s'" % (source, target))

        if self.isdir(target):
            target = os.path.join(target, os.path.basename(source))

        if not os.path.isdir(source):
            self.sftp.put(source, target)
            return

        for rootdir, subdirs, files in os.walk(source):
            targetdir = os.path.normpath(os.path.join(target, os.path.relpath(rootdir, source)))

            self.sftp.mkdir(targetdir)

            for entry in files:
                local_path  = os.path.join(rootdir, entry)
                remote_path = os.path.join(targetdir, entry)
                self.sftp.put(local_path, remote_path)

    def exists(self, path):
        try:
            self.sftp.lstat(path)
            return True
        except IOError:
            return False

    def isfile(self, path):
        try:
            attrs = self.sftp.lstat(path)
            return attrs.st_mode & stat.S_IFREG != 0
        except IOError:
            return False

    def isdir(self, path):
        try:
            attrs = self.sftp.lstat(path)
            return attrs.st_mode & stat.S_IFDIR != 0
        except IOError:
            return False


def ssh(*args, **kwargs):
    return SSHClient(*args, **kwargs)


def xmlrpctoken(uri, login, password):
    server = xmlrpclib.Server(uri)
    try:
        return server.login(login, password)
    except:
        raise AuthenticationError, "Error occured while login process"

def xmlrpcmethod(uri, method):
    server = xmlrpclib.Server(uri)
    try:
        return getattr(server, method)
    except:
        raise AttributeError, "Error occured while getting server method"
        

