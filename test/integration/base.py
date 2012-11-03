import logging

from unittest.case import TestCase

from integration import ci
from helpers import HTTPClient, SSHClient
logging.basicConfig(format=':%(lineno)d: %(asctime)s %(message)s',
                    level=logging.DEBUG)


class Base(TestCase):
    @classmethod
    def setUpClass(cls):
        logging.info("Waiting while bootstrapping is in progress")
        ssh = SSHClient()
        logpath = "/var/log/puppet/firstboot.log"
        str_success = "Finished catalog run"

        ssh.connect_ssh(str(ci.environment.node['admin'].ip_address), "root", "r00tme")
        count = 0
        while True:
            res = ssh.execute("grep '%s' '%s'" % (str_success, logpath))
            count += 1
            if not res['exit_status']:
                break
            sleep(5)
            if count == 200:
                raise Exception("Admin node bootstrapping has not finished or failed. \
                                 Check %s manually." % logpath)
        ssh.disconnect()

    def get_admin_node_ip(self):
        return str(ci.environment.node['admin'].ip_address)

    def get_id_by_mac(self, mac_address):
        return mac_address.replace(":", "").upper()
