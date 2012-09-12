import ipaddr
from itertools import chain

IPv4Address = ipaddr.IPv4Address
IPv4Network = ipaddr.IPv4Network


class NetworkPoolException(Exception):
    pass


class IpNetworksPool:
    def __init__(self, net_addresses=None, prefix=24):
        if not net_addresses:
            net_addresses = ['10.0.0.0/20']
        networks = []
        for address in net_addresses:
            if not isinstance(address, IPv4Network):
                address = IPv4Network(str(address))
            networks.append(address)

        self._available_networks = set(chain(
            *[net_address.iter_subnets(new_prefix=prefix) for net_address in
              networks]))
        self._allocated_networks = set()

    def reserve(self, network):
        for overlaping_network in filter(
            lambda n: n.overlaps(network),
            self._available_networks
        ):
            self._available_networks.remove(overlaping_network)

    def get(self):
        "get() - allocates and returns network address"
        x = self._available_networks.pop()
        self._allocated_networks.add(x)
        return x

    def put(self, network):
        "put(net_address) - return network address to pool"
        x = network
        if x not in self._allocated_networks:
            raise NetworkPoolException, "Network address '%s' wasn't previously allocated" % str(
                network)

        self._allocated_networks.remove(x)
        self._available_networks.add(x)

    @property
    def is_empty(self):
        return len(self._available_networks) == 0
