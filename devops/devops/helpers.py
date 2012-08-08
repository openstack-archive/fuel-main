import os
import os.path
import urllib
import stat
import socket
import time
import httplib
import xmlrpclib
import paramiko
import string
import random
from threading import Thread

import BaseHTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
import posixpath

import logging
logger = logging.getLogger('devops.helpers')

class TimeoutError(Exception): pass
class AuthenticationError(Exception): pass

def get_free_port():
    ports = range(32000, 32100)
    random.shuffle(ports)
    for port in ports:
        if not tcp_ping('localhost', port):
            return port
    raise Error, "No free ports available"

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
        self._sftp.close()
        self._ssh.close()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        pass

    def reconnect(self):
        self._ssh = paramiko.SSHClient()
        self._ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self._ssh.connect(self.host, port=self.port, username=self.username, password=self.password)
        self._sftp = self._ssh.open_sftp()

    def execute(self, command):
        logger.debug("Executing command: '%s'" % command.rstrip())
        chan = self._ssh.get_transport().open_session()
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

        chan.close()

        return result

    def mkdir(self, path):
        if self.exists(path):
            return
        logger.debug("Creating directory: %s" % path)
        self.execute("mkdir %s\n" % path)

    def rm_rf(self, path):
        logger.debug("Removing directory: %s" % path)
        self.execute("rm -rf %s" % path)

    def open(self, path, mode='r'):
        return self._sftp.open(path, mode)

    def upload(self, source, target):
        logger.debug("Copying '%s' -> '%s'" % (source, target))

        if self.isdir(target):
            target = os.path.join(target, os.path.basename(source))

        if not os.path.isdir(source):
            self._sftp.put(source, target)
            return

        for rootdir, subdirs, files in os.walk(source):
            targetdir = os.path.normpath(os.path.join(target, os.path.relpath(rootdir, source)))

            self.mkdir(targetdir)

            for entry in files:
                local_path  = os.path.join(rootdir, entry)
                remote_path = os.path.join(targetdir, entry)
                if not self.exists(remote_path):
                    self._sftp.put(local_path, remote_path)

    def exists(self, path):
        try:
            self._sftp.lstat(path)
            return True
        except IOError:
            return False

    def isfile(self, path):
        try:
            attrs = self._sftp.lstat(path)
            return attrs.st_mode & stat.S_IFREG != 0
        except IOError:
            return False

    def isdir(self, path):
        try:
            attrs = self._sftp.lstat(path)
            return attrs.st_mode & stat.S_IFDIR != 0
        except IOError:
            return False


def ssh(*args, **kwargs):
    return SSHClient(*args, **kwargs)



class HttpServer:
    class Handler(SimpleHTTPRequestHandler):
        logger = logging.getLogger('devops.helpers.http_server')

        def __init__(self, docroot, *args, **kwargs):
            self.docroot = docroot
            SimpleHTTPRequestHandler.__init__(self, *args, **kwargs)

        # Suppress reverse DNS lookups to speed up processing
        def address_string(self):
            return self.client_address[0]

        # Handle docroot
        def translate_path(self, path):
            """Translate a /-separated PATH to the local filename syntax.

            Components that mean special things to the local file system
            (e.g. drive or directory names) are ignored.  (XXX They should
            probably be diagnosed.)

            """
            # abandon query parameters
            path = path.split('?',1)[0]
            path = path.split('#',1)[0]
            path = posixpath.normpath(urllib.unquote(path))
            words = path.split('/')
            words = filter(None, words)
            path = self.docroot
            for word in words:
                drive, word = os.path.splitdrive(word)
                head, word = os.path.split(word)
                path = os.path.join(path, word)
            return path

        def log_message(self, format, *args):
            self.logger.info(format % args)

    def __init__(self, document_root):
        self.port = get_free_port()
        self.document_root = document_root

        def handler_factory(*args, **kwargs):
            return HttpServer.Handler(document_root, *args, **kwargs)

        self._server = BaseHTTPServer.HTTPServer(('', self.port), handler_factory)
        self._thread = Thread(target=self._server.serve_forever)
        self._thread.daemon = True

    def start(self):
        self._thread.start()

    def run(self):
        self._thread.join()

    def stop(self):
        self._server.shutdown()
        self._thread.join()

def http_server(document_root):
    server = HttpServer(document_root)
    server.start()
    return server


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
        

