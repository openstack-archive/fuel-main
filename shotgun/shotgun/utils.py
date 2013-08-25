import socket
import re


def hostname():
    return socket.gethostname()


def is_ip(name):
    return (re.search(ur"([0-9]{1,3}\.){3}[0-9]{1,3}", name) and True)


def fqdn(name=None):
    if name:
        return socket.getfqdn(name)
    return socket.getfqdn(socket.gethostname())


def is_local(name):
    if name in ("localhost", hostname(), fqdn()):
        return True
    return False
