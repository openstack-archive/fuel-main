import xmlrpclib
import logging
from time import sleep
from unittest import TestCase

from . import ci
from devops.helpers import wait, tcp_ping, http, ssh
from integration.helpers import SSHClient

logging.basicConfig(format=':%(lineno)d: %(asctime)s %(message)s', level=logging.DEBUG)

class TestCobbler(TestCase):
    def __init__(self, *args, **kwargs):
        super(TestCobbler, self).__init__(*args, **kwargs)
        self.remote = SSHClient()
        self.logpath = "/var/log/chef/solo.log"
        self.str_success = "Report handlers complete"

    def setUp(self):
        self.ip = ci.environment.node['admin'].ip_address

    def test_cobbler_alive(self):
        logging.info("Waiting for handlers to complete")

        self.remote.connect_ssh(str(self.ip), "ubuntu", "r00tme")
        count = 0
        while True:
            res = self.remote.exec_cmd("grep '%s' '%s'" % (self.str_success, self.logpath))
            count += 1
            if res['exit_status'] == 0:
                break
            sleep(5)
            if count == 200:
                raise Exception("Chef handlers failed to complete")
        self.remote.disconnect()

        wait(lambda: http(host=self.ip, url='/cobbler_api', waited_code=501), timeout=60)
        server = xmlrpclib.Server('http://%s/cobbler_api' % self.ip)
        token = server.login('cobbler', 'cobbler')
        assert server.ping() == True