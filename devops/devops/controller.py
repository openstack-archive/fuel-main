import os
import tempfile

from model import Node, Network

class Controller:
    def __init__(self, driver):
        self.driver = driver
        self.home_dir = os.environ.get('DEVOPS_HOME') or os.path.join(os.environ['HOME'], ".devops")
        if not os.path.exists(self.home_dir):
            os.system("mkdir -p '%s'" % self.home_dir)

    def build_environment(self, environment):
        environment.work_dir = tempfile.mkdtemp(prefix=os.path.join(self.home_dir, 'environments', environment.name)+'-')

        if not os.path.exists(environment.work_dir):
            os.system("mkdir -p '%s'" % environment.work_dir)

        environment.driver = self.driver

        for network in environment.networks:
            self._build_network(environment, network)
            network.driver = self.driver
            network.start()

        for node in environment.nodes:
            self._build_node(environment, node)
            node.driver = self.driver

    def destroy_environment(self, environment):
        for node in environment.nodes:
            node.stop()
            self.driver.delete_node(node)
            del node.driver

        for network in environment.networks:
            network.stop()
            self.driver.delete_network(network)
            del network.driver

        del environment.driver

    def _build_network(self, environment, network):
        self.driver.create_network(network)

    def _build_node(self, environment, node):
        for disk in node.disks:
            if disk.path is None:
                fd, disk.path = tempfile.mkstemp(prefix=environment.work_dir+'/', suffix='.' + disk.format)
                os.close(fd)
            self.driver.create_disk(disk)

        self.driver.create_node(node)

