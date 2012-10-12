# -*- coding: utf-8 -*-

import os

LOGFILE = "nailgun.log"

COBBLER_URL = "http://localhost/cobbler_api"
COBBLER_USER = "cobbler"
COBBLER_PASSWORD = "cobbler"
COBBLER_PROFILE = "centos-6.3-x86_64"

home = os.getenv("HOME")
PATH_TO_SSH_KEY = home and os.path.join(home, ".ssh", "id_rsa") or None
PATH_TO_BOOTSTRAP_SSH_KEY = home and \
    os.path.join(home, ".ssh", "bootstrap.rsa") or None

MCO_PSKEY = "Gie6iega9ohngaenahthohngu8aebohxah9seidi"
MCO_STOMPHOST = "localhost"
MCO_STOMPPORT = "61613"
MCO_STOMPUSER = "guest"
MCO_STOMPPASSWORD = "guest"

PUPPET_MASTER_HOST = "localhost"
PUPPET_VERSION = "2.7.19"

DNS_DOMAIN = "example.com"
DNS_SERVERS = "127.0.0.1"
DNS_SEARCH = "example.com"
