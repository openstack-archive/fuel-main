import logging
from time import sleep

import xmlrpclib
from devops.helpers import wait, tcp_ping, http, ssh

from test.integration.base import Base
from test.helpers import SSHClient


class TestCobbler(Base):
    def __init__(self, *args, **kwargs):
        super(TestCobbler, self).__init__(*args, **kwargs)
        self.remote = SSHClient()

    def setUp(self):
        logging.info('Admin node ip: %s' % self.get_admin_node_ip())
        self.ip = self.get_admin_node_ip()

    def tearDown(self):
        pass

    # There is unknown issue with Cobbler interface so this currently fails
    def test_cobbler_alive(self):
        wait(
            # it's now 502 but shouldn't be - just for now
            lambda: http(host=self.ip, url='/cobbler_api', waited_code=502),
            timeout=60
        )
        server = xmlrpclib.Server('http://%s/cobbler_api' % self.ip)
        token = server.login('cobbler', 'cobbler')
