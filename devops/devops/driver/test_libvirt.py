import unittest
from lxml import etree
from devops.model import Network, Node
from devops.driver.libvirt import Libvirt, LibvirtXMLBuilder

class TestLibvirtXMLBuilder(unittest.TestCase):
    def setUp(self):
        self.builder = LibvirtXMLBuilder()

    def test_hostonly_network_xml_generation(self):
        network = Network('net1')
        network.id = 'net1'
        xml = self.builder.build_network_xml(network)

        doc = etree.fromstring(xml)

        self.assertIsNotNone(doc)
        self.assertEqual('network', doc.tag)
        
        e = doc.find('name')
        self.assertIsNotNone(e)
        self.assertEqual('net1', e.text)

        # e = doc.find('bridge')
        # self.assertIsNotNone(e)
        # self.assertEqual('bridge-net1', e.get('name'))
