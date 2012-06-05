import unittest
import devops
from devops.helpers import wait
import os
import time

class TestNodeIpAddress(unittest.TestCase):
    def setUp(self):
        self.env = devops.load("""
            networks:
              - network: net1
                dhcp_server: True
            nodes:
              - node: foo
                networks: net1
                cdrom: http://mc0n1-srt.srt.mirantis.net/livecd.iso
                vnc: True
        """)
        devops.build(self.env)

    def tearDown(self):
        devops.destroy(self.env)

    def test_ip_address_detection(self):
        node = self.env.nodes[0]
        node.start()
        time.sleep(10)
        node.send_keys('<Enter>')
        wait(lambda: len(node.ip_addresses) > 0, timeout=60)

