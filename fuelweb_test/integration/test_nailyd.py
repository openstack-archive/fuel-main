import logging

import xmlrpclib

from fuelweb_test.integration.base import Base
from fuelweb_test.helpers import SSHClient


class TestNailyd(Base):
    def __init__(self, *args, **kwargs):
        super(TestNailyd, self).__init__(*args, **kwargs)
        self.remote = SSHClient()

    def setUp(self):
        logging.info('Admin node ip: %s' % self.get_admin_node_ip())
        self.ip = self.get_admin_node_ip()

    def tearDown(self):
        pass

    def test_nailyd_alive(self):
        self.remote.connect_ssh(self.ip, 'root', 'r00tme')
        ps_output = self.remote.execute('ps ax')['stdout']
        naily_processes = filter(lambda x: 'naily master' in x, ps_output)
        logging.debug("Found %d naily master processes: %s" %
                      (len(naily_processes), naily_processes))
        self.assertEqual(1, len(naily_processes))
        naily_processes = filter(lambda x: 'naily worker' in x, ps_output)
        logging.debug("Found %d naily worker processes: %s" %
                      (len(naily_processes), naily_processes))
        self.assertEqual(True, len(naily_processes) > 1)
