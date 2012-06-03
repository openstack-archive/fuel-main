import unittest
from devops.network import IpNetworksPool, IPv4Network, NetworkPoolException

class TestIpNetworksPool(unittest.TestCase):
    def test_getting_subnetworks(self):

        n = IpNetworksPool(net_addresses=['10.1.0.0/22'], prefix=24)

        nets = []
        while not n.is_empty:
            nets.append(n.get())

        self.assertEqual(4, len(nets))
        self.assertTrue(IPv4Network('10.1.0.0/24') in nets)
        self.assertTrue(IPv4Network('10.1.1.0/24') in nets)
        self.assertTrue(IPv4Network('10.1.2.0/24') in nets)
        self.assertTrue(IPv4Network('10.1.3.0/24') in nets)

    def test_putting_back(self):
        n = IpNetworksPool(net_addresses=['10.1.0.0/22'], prefix=24)

        while not n.is_empty:
            n.get()

        self.assertTrue(n.is_empty)

        n.put(IPv4Network('10.1.1.0/24'))

        self.assertFalse(n.is_empty)

        self.assertEqual(IPv4Network('10.1.1.0/24'), n.get())

        self.assertTrue(n.is_empty)

    def test_putting_back_network_not_from_this_pool_raises_error(self):
        n = IpNetworksPool(net_addresses=['10.1.0.0/22'], prefix=24)
        while not n.is_empty:
            n.get()

        with self.assertRaises(NetworkPoolException):
            n.put(IPv4Network('10.2.1.0/24'))

