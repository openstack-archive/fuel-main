
class ManagedObject(object):
    def __init__(self):
        super(ManagedObject, self).__init__()
        self._driver = None

    @property
    def driver(self):
        if self._driver is None:
            raise EnvironmentException, "Network '%s' wasn't built yet" % self.name
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
    def __init__(self, name, dhcp_server=False):
        super(Network, self).__init__()

        self.name = name
        self.dhcp_server = dhcp_server

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

    def send_keys(self, keys):
        self.driver.send_keys_to_node(self, keys)

class Cdrom(object):
    def __init__(self, isopath=None, bus='ide'):
        self.isopath = isopath
        self.bus = bus

class Disk(object):
    def __init__(self, size, format='qcow2', bus='ide'):
        self.size = size
        self.format = format
        self.bus = bus
        self.path = None

class Interface(object):
    def __init__(self, network):
        self.network = network

