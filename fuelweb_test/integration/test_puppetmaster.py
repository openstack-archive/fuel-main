import logging

import xmlrpclib
from devops.helpers import wait, tcp_ping

from fuelweb_test.integration.base import Base
from fuelweb_test.helpers import SSHClient


class TestPuppetMaster(Base):
    def __init__(self, *args, **kwargs):
        super(TestPuppetMaster, self).__init__(*args, **kwargs)
        self.remote = SSHClient()

    def setUp(self):
        logging.info('Admin node ip: %s' % self.get_admin_node_ip())
        self.ip = self.get_admin_node_ip()

    def tearDown(self):
        pass

    def test_puppetmaster_alive(self):
        wait(
            lambda: tcp_ping(self.ip, 8140),
            timeout=5
        )
        self.remote.connect_ssh(self.ip, 'root', 'r00tme')
        ps_output = self.remote.execute('ps ax')['stdout']
        pm_processes = filter(
            lambda x: '/usr/sbin/puppetmasterd' in x,
            ps_output
        )
        logging.debug("Found puppet master processes: %s" % pm_processes)
        self.assertEquals(len(pm_processes), 4)
