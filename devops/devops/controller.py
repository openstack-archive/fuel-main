import os
import sys
import stat
import tempfile
import shutil
import ipaddr

from devops.model import Node, Network
from devops.network import IpNetworksPool

class Controller:
    def __init__(self, driver):
        self.driver = driver

        self.networks_pool = IpNetworksPool()
        self._reserve_networks()

        self.home_dir = os.environ.get('DEVOPS_HOME') or os.path.join(os.environ['HOME'], ".devops")
        try:
            os.makedirs(os.path.join(self.home_dir, 'environments'), 0755)
        except OSError:
            sys.exc_clear()

    def build_environment(self, environment):
        environment.work_dir = tempfile.mkdtemp(prefix=os.path.join(self.home_dir, 'environments', environment.name)+'-')
        os.chmod(environment.work_dir, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

        environment.driver = self.driver

        for network in environment.networks:
            network.ip_addresses = self.networks_pool.get()
            self.driver.create_network(network)
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
            self.networks_pool.put(network.ip_addresses)

        del environment.driver

        shutil.rmtree(environment.work_dir)

    def _reserve_networks(self):
        with os.popen("ip route") as f:
            for line in f:
                words = line.split()
                if len(words) == 0:
                    continue
                if words[0] == 'default':
                    continue
                address = ipaddr.IPv4Network(words[0])
                self.networks_pool.reserve(address)

    def _build_network(self, environment, network):
        network.ip_addresses = self.networks_pool.get()

        self.driver.create_network(network)

    def _build_node(self, environment, node):
        for disk in filter(lambda d: d.path is None, node.disks):
            fd, disk.path = tempfile.mkstemp(
                prefix=environment.work_dir + '/disk',
                suffix='.' + disk.format
            )
            os.close(fd)
            self.driver.create_disk(disk)

        self.driver.create_node(node)

