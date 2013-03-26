import logging
import time

from unittest.case import TestCase

from fuelweb_test.integration import ci
from fuelweb_test.helpers import HTTPClient, SSHClient
logging.basicConfig(format=':%(lineno)d: %(asctime)s %(message)s',
                    level=logging.DEBUG)


class Base(TestCase):
    @classmethod
    def setUpClass(cls):
        pass

    def get_admin_node_ip(self):
        return str(ci.environment.node['admin'].ip_address)

    def get_host_hode_ip(self):
        return str(ci.environment.networks[0].ip_addresses[1])

    def _wait_for_threads(self):
        import threading
        for thread in threading.enumerate():
            if thread is not threading.currentThread():
                if hasattr(thread, "rude_join"):
                    timer = time.time()
                    timeout = 25
                    thread.rude_join(timeout)
                    if time.time() - timer > timeout:
                        raise Exception("Thread stopping timed out")
