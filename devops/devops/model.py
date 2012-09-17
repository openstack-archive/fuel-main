from itertools import chain


class EnvironmentException(object):
    pass


class ManagedObject(object):
    def __init__(self):
        super(ManagedObject, self).__init__()
        self._driver = None
        self.name = None

    @property
    def driver(self):
        if self._driver is None:
            raise EnvironmentException, "Object '%s' wasn't built yet" % self.name
        return self._driver

    @driver.setter
    def driver(self, driver):
        self._driver = driver

    @driver.deleter
    def driver(self):
        del self._driver


class Environment(ManagedObject):
    def __init__(self, name):
        super(Environment, self).__init__()

        self.name = name
        self.networks = []
        self.nodes = []
        self.built = False

    @property
    def node(self):
        name2node = {}
        for node in self.nodes:
            name2node[node.name] = node
        return name2node

    @property
    def network(self):
        name2network = {}
        for network in self.networks:
            name2network[network.name] = network
        return name2network


class Network(ManagedObject):
    def __init__(self, name, dhcp_server=False, pxe=False):
        super(Network, self).__init__()

        self.name = name
        self.dhcp_server = dhcp_server
        self.interfaces = []
        self.pxe = pxe

    def start(self):
        self.driver.start_network(self)

    def stop(self):
        self.driver.stop_network(self)


class Node(ManagedObject):
    def __init__(self, name, cpu=1, memory=512, arch='x86_64', vnc=False):
        super(Node, self).__init__()

        self.name = name

        self.cpu = cpu
        self.memory = memory
        self.arch = arch
        self.vnc = vnc
        self.interfaces = []
        self.disks = []
        self.boot = []
        self.cdrom = None

    def start(self):
        self.driver.start_node(self)

    def stop(self):
        self.driver.stop_node(self)

    def reset(self):
        self.driver.reset_node(self)

    def reboot(self):
        self.driver.reboot_node(self)

    def shutdown(self):
        self.driver.shutdown_node(self)

    @property
    def snapshots(self):
        return self.driver.get_node_snapshots(self)

    def has_snapshot(self, snapshot_name):
        return snapshot_name in self.snapshots

    def save_snapshot(self, name=None, force=False):
        "Create node state snapshot. Returns snapshot name"
        if name and force and self.has_snapshot(name):
            self.delete_snapshot(name)
        return self.driver.create_snapshot(self, name=name)

    def restore_snapshot(self, snapshot_name=None):
        "Revert node state to given snapshot. If no snapshot name given, revert to current snapshot."
        self.driver.revert_snapshot(self, snapshot_name)

    def delete_snapshot(self, snapshot_name=None):
        "Delete snapshot. If no snapshot name given, delete current snapshot."
        self.driver.delete_snapshot(self, snapshot_name)

    def send_keys(self, keys):
        self.driver.send_keys_to_node(self, keys)

    @property
    def ip_addresses(self):
        addresses = []
        for interface in self.interfaces:
            addresses += interface.ip_addresses
        return addresses

    @property
    def ip_address(self):
        x = self.ip_addresses
        if len(x) == 0:
            return None
        return x[0]

    @ManagedObject.driver.setter
    def driver(self, driver):
        ManagedObject.driver.fset(self, driver)
        for interface in self.interfaces:
            interface.driver = driver


class Cdrom(object):
    def __init__(self, isopath=None, bus='ide'):
        self.isopath = isopath
        self.bus = bus


class Disk(object):
    def __init__(self, size=None, path=None, format='qcow2', bus='ide',
                 base_image=None):
        self.size = size
        self.format = format
        self.bus = bus
        self.path = path
        # Either copy or use "backing file" feature
        self.base_image = base_image


class Interface(ManagedObject):
    def __init__(self, network, ip_addresses=None):
        if not ip_addresses: ip_addresses = []
        self.node = None
        self.network = network
        if not isinstance(ip_addresses, (list, tuple)):
            ip_addresses = (ip_addresses,)
        self._ip_addresses = ip_addresses
        self.mac_address = None

    @property
    def ip_addresses(self):
        return self._ip_addresses

    @ip_addresses.setter
    def ip_addresses(self, value):
        if not isinstance(value, (list, tuple)):
            value = (value,)
        self._ip_addresses = value
