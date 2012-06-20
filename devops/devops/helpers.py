import os
import socket
import time
import httplib
import xmlrpclib
import paramiko
import string

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
    
class Ssh:
    def __init__(self, hostname, port=22, username=None, 
                 password=None, pkey=None, 
                 key_filename=None, timeout=None):

        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.pkey = pkey
        self.key_filename = key_filename
        self.timeout = timeout

        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(KeyPolicy())
        
    def connect(self):
        self.ssh.connect(self.hostname, port=self.port, username=self.username, 
                         password=self.password, pkey=self.pkey, 
                         key_filename=self.key_filename, timeout=self.timeout)

    def __enter__(self):
        self.connect()
        return self.ssh

    def __exit__(self, type, value, traceback):
        self.ssh.close()


def ssh(hostname, command, port=22, username=None, 
        password=None, pkey=None, key_filename=None, timeout=None, outerr=False):

    rsout = []
    rserr = []

    with Ssh(hostname, port=port, username=username, 
             password=password, pkey=pkey, 
             key_filename=key_filename, timeout=timeout) as s:
        if outerr:
            (sin, sout, sout) = s.exec_command(command)
        else:
            (sin, sout, serr) = s.exec_command(command)

            for line in serr.readlines():
                line = string.strip(line)
                rserr.append(line)

        for line in sout.readlines():
            line = string.strip(line)
            rsout.append(line)

    return {'out':rsout, 'err':rserr}


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
        

