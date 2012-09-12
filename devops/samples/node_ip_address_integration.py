import unittest
import devops
from devops.helpers import wait, TimeoutError
import time

ISO_URL = 'http://mc0n1-srt.srt.mirantis.net/livecd.iso'


class TestNodeIpAddress(unittest.TestCase):
    def setUp(self):
        self.env = devops.load("""
            networks:
              - network: net1
                dhcp_server: True
            nodes:
              - node: foo
                networks: net1
                cdrom: '%s'
                vnc: True
        """ % ISO_URL)
        devops.build(self.env)

    def tearDown(self):
        devops.destroy(self.env)

    def test_ip_address_detection(self):
        node = self.env.nodes[0]
        network = self.env.networks[0]

        node.start()
        # Wait for ISOLINUX to boot
        time.sleep(10)
        # Trigger ISOLINUX menu selection
        node.send_keys('<Enter>')

        try:
            wait(lambda: len(node.ip_addresses) > 0, timeout=60)
        except TimeoutError:
            self.fail("Node didn't get ip_address in specified amount of time")

        self.assertEqual(node.ip_address, node.ip_addresses[0])
        self.assertTrue(node.ip_address in network.ip_addresses)
