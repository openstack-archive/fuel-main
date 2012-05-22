import os
import tempfile

from model import Node, Network

class Controller:
    def __init__(self, environment, driver):
        self.environment = environment
        self.driver = driver
        self.home_dir = os.environ.get('DEVOPS_HOME') or os.path.join(os.environ['HOME'], ".devops")
        if not os.path.exists(self.home_dir):
            os.system("mkdir -p '%s'" % self.home_dir)

        self.env_dir = tempfile.mkdtemp(prefix=os.path.join(self.home_dir, 'environments')+'/', suffix='-'+self.environment.name)

    def build_environment(self):
        if not os.path.exists(os.path.join(self.home_dir, 'environments')):
            os.system("mkdir -p '%s'" % os.path.join(self.home_dir, 'environments'))

        for network in self.environment.networks:
            self._build_network(network)
            self.driver.start_network(network)

        for node in self.environment.nodes:
            self._build_node(node)

    def destroy_environment(self):
        for node in self.environment.nodes:
            self.driver.stop_node(node)
            self.driver.delete_node(node)

        for network in self.environment.networks:
            self.driver.stop_network(network)
            self.driver.delete_network(network)

    def start(self, o):
        if isinstance(o, Node):
            self.start_node(o)
        elif isinstance(o, Network):
            self.driver.start_network(o)
        else:
            raise "Unknown object %s" % o

    def start_node(self, node):
        if type(node) == str:
            for n in self.environment.nodes:
                if n.name == node:
                    node = n
                    break

        if not isinstance(node, Node):
            raise "Unknown node %s" % node

        self.driver.start_node(node)

    def stop(self, o):
        if isinstance(o, Node):
            self.driver.stop_node(o)
        elif isinstance(o. Network):
            self.driver.stop_network(o)
        else:
            raise "Unknown object %s" % o

    def stop_node(self, node):
        if type(node) == str:
            for n in self.environment.nodes:
                if n.name == node:
                    node = n
                    break

        if not isinstance(node, Node):
            raise "Unknown node %s" % node

        self.driver.stop_node(node)

    def _build_network(self, network):
        self.driver.create_network(network)

    def _build_node(self, node):
        for disk in node.disks:
            if disk.path is None:
                fd, disk.path = tempfile.mkstemp(prefix=self.env_dir+'/', suffix='.' + disk.format)
                os.close(fd)
            self.driver.create_disk(disk)

        self.driver.create_node(node)

