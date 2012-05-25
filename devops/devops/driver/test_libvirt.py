import unittest
from devops import xml
from devops.model import Network, Node, Disk, Cdrom
from devops.driver.libvirt import Libvirt, LibvirtXMLBuilder, DeploymentSpec


class TestLibvirtXMLBuilder(unittest.TestCase):
    node_spec = DeploymentSpec()
    node_spec.arch = 'x86_64'
    node_spec.os_type = 'hvm'
    node_spec.hypervisor = 'kvm'
    node_spec.emulator = '/usr/bin/kvm'

    def setUp(self):
        self.builder = LibvirtXMLBuilder()

    def test_hostonly_network_xml_generation(self):
        network = Network('net1')
        network.id = 'net1'
        doc_xml = self.builder.build_network_xml(network)

        doc = xml.parse_string(doc_xml)

        self.assertIsNotNone(doc)
        self.assertEqual('network', doc.tag)
        
        e = doc.find('name')
        self.assertIsNotNone(e)
        self.assertEqual('net1', e.text)

    def test_node_memory(self):
        node = Node('node1')
        node.id = node.name
        node.memory = 123
        
        doc_xml = self.builder.build_node_xml(node, self.node_spec)

        doc = xml.parse_string(doc_xml)

        memory_element = doc.find('memory')
        self.assertIsNotNone(memory_element)
        self.assertEqual('KiB', memory_element['unit'])
        self.assertEqual(str(123*1024), memory_element.text)


    def test_cdrom_disk(self):
        node = Node('node1')
        node.id = node.name
        node.cdrom = Cdrom(isopath='foo.iso')

        doc_xml = self.builder.build_node_xml(node, self.node_spec)

        doc = xml.parse_string(doc_xml)

        cdrom_element = doc.find('devices/disk[@type="file" and @device="cdrom"]')
        self.assertIsNotNone(cdrom_element)

        cdrom_driver_element = cdrom_element.find('driver')
        self.assertIsNotNone(cdrom_driver_element)
        self.assertEqual('qemu', cdrom_driver_element['name'])
        self.assertEqual('raw', cdrom_driver_element['type'])

        cdrom_source_element = cdrom_element.find('source')
        self.assertIsNotNone(cdrom_source_element)
        self.assertEqual('foo.iso', cdrom_source_element['file'])

