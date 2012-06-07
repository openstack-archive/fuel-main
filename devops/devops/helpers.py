import os
import socket
import time
import httplib
import xmlrpclib

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
      wait(predicate, interval=5, timeout=None) - wait until predicate will become True.
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

def http(host='localhost', port=80, method='GET', url='/', waited_code=200):
    conn = httplib.HTTPConnection(host, port)
    conn.request(method, url)
    res = conn.getresponse()
    
    if res.status == waited_code:
        return True
    return False

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
        
