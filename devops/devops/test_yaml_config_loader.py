import unittest
from devops import yaml_config_loader

class TestYamlConfigLoader(unittest.TestCase):
    def test_nodes(self):
        doc = """
nodes:
  -
    name: node1
  -
    name: node2
        """
        env = self.load(doc)

        self.assertEqual(2, len(env.nodes))
        self.assertEqual("node1", env.nodes[0].name)
        self.assertEqual("node2", env.nodes[1].name)

    def test_networks(self):
        doc = """
networks:
  -
    name: net1
  -
    name: net2

nodes:
  - name: foo
        """
        env = self.load(doc)
        
        self.assertEqual(2, len(env.networks))
        self.assertEqual("net1", env.networks[0].name)
        self.assertEqual("net2", env.networks[1].name)

    def test_network_dhcp_server(self):
        doc = """
networks:
  - name: managed
    dhcp_server: True
  - name: unmanaged
nodes:
  - name: foo
        """
        env = self.load(doc)
        self.assertTrue(env.networks[0].dhcp_server)
        self.assertFalse(env.networks[1].dhcp_server)

    def test_disk_size(self):
        doc = """
nodes:
  - name: foo
    disk: 8Gb
        """
        env = self.load(doc)

        self.assertEqual(1, len(env.nodes[0].disks))
        disk = env.nodes[0].disks[0]
        self.assertEqual(8*1024**3, disk.size)
        self.assertIsNone(disk.path)

    def test_disk_path(self):
        doc = """
nodes:
  - name: foo
    disk: /tmp/foo.qcow2
        """
        env = self.load(doc)

        self.assertEqual(1, len(env.nodes[0].disks))
        disk = env.nodes[0].disks[0]
        self.assertEqual('/tmp/foo.qcow2', disk.path)
        self.assertIsNone(disk.size)

    def load(self, data):
        return yaml_config_loader.load(data)

