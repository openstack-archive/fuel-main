from unittest.case import TestCase
from integration import ci
from helpers import HTTPClient
import logging
logging.basicConfig(format=':%(lineno)d: %(asctime)s %(message)s', level=logging.DEBUG)

class Base(TestCase):

    client = HTTPClient()

    def get_admin_node_ip(self):
        if ci is not None and ci.environment is not None:
            return ci.environment.node['admin'].ip_address
        else:
            return "10.20.0.2"

    def get_id_by_mac(self, mac_address):
        return mac_address.replace(":", "").upper()

#    def getSlaveNodeIp(self, getIdByMac):


