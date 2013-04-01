from abc import abstractproperty, abstractmethod
from devops.helpers.helpers import _get_file_size
from devops.manager import Manager
from ipaddr import IPNetwork
from fuelweb_test.node_roles import Nodes
from fuelweb_test.settings import EMPTY_SNAPSHOT, ISO


class CiBase(object):
    def __init__(self):
        self.manager = Manager()
        self._environment = None

    def _get_or_create(self):
        try:
            return self.manager.environment_get(self.env_name())
        except:
            self._environment = self.describe_environment()
            self._environment.define()
            return self._environment

    def get_empty_state(self):
        if self.environment().has_snapshot(EMPTY_SNAPSHOT):
            self.environment().revert(EMPTY_SNAPSHOT)
        else:
            self.setup_environment()

    def environment(self):
        """
        :rtype : devops.models.Environment
        """
        self._environment = self._environment or self._get_or_create()
        return self._environment

    @abstractproperty
    def env_name(self):
        """
        :rtype : string
        """
        pass

    @abstractmethod
    def describe_environment(self):
        """
        :rtype : devops.models.Environment
        """
        pass

    @abstractproperty
    def node_roles(self):
        """
        :rtype : NodeRoles
        """
        pass

    def nodes(self):
        return Nodes(self.environment(), self.node_roles())

    # noinspection PyShadowingBuiltins
    def add_empty_volume(self, node, name, capacity=20 * 1024 * 1024 * 1024,
                         device='disk', bus='virtio', format='qcow2'):
        self.manager.node_attach_volume(
            node=node,
            volume=self.manager.volume_create(
                name=name, capacity=capacity,
                environment=self.environment(),
                format=format),
            device=device, bus=bus)

    def add_node(self, memory, name, boot=None):
        return self.manager.node_create(
            name=name,
            memory=memory,
            environment=self.environment(),
            boot=boot)

    def create_interfaces(self, networks, node):
        for network in networks:
            if network.name == 'internal':
                self.manager.interface_create(network, node=node)
                self.manager.interface_create(network, node=node)
            self.manager.interface_create(network, node=node)

    def describe_admin_node(self, name, networks, memory=1024):
        node = self.add_node(memory=memory, name=name, boot=['hd', 'cdrom'])
        self.create_interfaces(networks, node)
        self.add_empty_volume(node, name + '-system')
        self.add_empty_volume(
            node, name + '-iso', capacity=_get_file_size(ISO),
            format='raw', device='cdrom', bus='ide')
        return node

    def describe_empty_node(self, name, networks, memory=1024):
        node = self.add_node(memory, name)
        self.create_interfaces(networks, node)
        self.add_empty_volume(node, name + '-system')
        self.add_empty_volume(node, name + '-cinder')
        self.add_empty_volume(node, name + '-swift')
        return node

    @abstractmethod
    def setup_environment(self):
        """
        :rtype : None
        """
        pass

    def internal_virtual_ip(self):
        return str(IPNetwork(
            self.environment().network_by_name('internal').ip_network)[-2])

    def public_router(self):
        return str(
            IPNetwork(
                self.environment().network_by_name('public').ip_network)[1])

    def internal_router(self):
        return str(
            IPNetwork(
                self.environment().network_by_name('internal').ip_network)[1])

    def get_host_node_ip(self):
        return self.internal_router()

    def internal_network(self):
        return str(
            IPNetwork(
                self.environment().network_by_name('internal').ip_network))

    def internal_net_mask(self):
        return str(IPNetwork(
            self.environment().network_by_name('internal').ip_network).netmask)

    def public_net_mask(self):
        return str(IPNetwork(
            self.environment().network_by_name('public').ip_network).netmask)

    def public_network(self):
        return str(
            IPNetwork(self.environment().network_by_name('public').ip_network))
