import logging
import time

from unittest.case import TestCase

from test.integration import ci
from test.helpers import HTTPClient, SSHClient
logging.basicConfig(format=':%(lineno)d: %(asctime)s %(message)s',
                    level=logging.DEBUG)


class Base(TestCase):
    @classmethod
    def setUpClass(cls):
        pass

    def get_admin_node_ip(self):
        return str(ci.environment.node['admin'].ip_address)

    def get_id_by_mac(self, mac_address):
        return mac_address.replace(":", "").upper()
