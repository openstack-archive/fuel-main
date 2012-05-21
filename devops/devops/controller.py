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

    def build_environment(self):
        if not os.path.exists(os.path.join(self.home_dir, 'environments')):
            os.system("mkdir -p '%s'" % os.path.join(self.home_dir, 'environments'))

        self.env_dir = tempfile.mkdtemp(prefix=os.path.join(self.home_dir, 'environments')+'/', suffix='-'+self.environment.name)
        self.environment.id = os.path.basename(self.env_dir)

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
            self.driver.start_node(o)
        elif isinstance(o, Network):
            self.driver.start_network(o)
        else:
            raise "Unknown object %s" % o

    def stop(self, o):
        if isinstance(o, Node):
            self.driver.stop_node(o)
        elif isinstance(o. Network):
            self.driver.stop_network(o)
        else:
            raise "Unknown object %s" % o

    def _build_network(self, network):
        network.id = "%s-%s" % (self.environment.id, network.name)

        self.driver.create_network(network)

    def _build_node(self, node):
        node.id = "%s-%s" % (self.environment.id, node.name)

        disk_count = 0
        for disk in node.disks:
            if disk.path is None:
                disc_count += 1
                disk.path = os.path.join(self.env_dir, "%s-%d" % (node.id, disc_count))
            print("Creating disk for node %s (id=%s), size=%s" % (node.name, node.id, disk.size))
            self.driver.create_disk(disk)

        self.driver.create_node(node)

