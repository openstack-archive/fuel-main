import logging
from abc import abstractproperty, abstractmethod
from devops.manager import Manager
from ipaddr import IPNetwork

class CiBase(object):
    def __init__(self):
        self.manager = Manager()
        self.base_image = self.manager.volume_get_predefined(BASE_IMAGE)
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

    def add_empty_volume(self, node, name):
        self.manager.node_attach_volume(
            node=node,
            volume=self.manager.volume_create(
                name=name, capacity=20 * 1024 * 1024 * 1024,
                environment=self.environment()))

    def add_node(self, memory, name):
        return self.manager.node_create(
            name=name,
            memory=memory,
            environment=self.environment())

    def describe_node(self, name, networks, memory=1024):
        node = self.add_node(memory, name)
        for network in networks:
            self.manager.interface_create(network, node=node)
        self.manager.node_attach_volume(
            node=node,
            volume=self.manager.volume_create_child(
                name=name + '-system', backing_store=self.base_image,
                environment=self.environment()))
        self.add_empty_volume(node, name + '-cinder')
        return node

    def describe_empty_node(self, name, networks, memory=1024):
        node = self.add_node(memory, name)
        for network in networks:
            self.manager.interface_create(network, node=node)
        self.add_empty_volume(node, name + '-system')
        self.add_empty_volume(node, name + '-cinder')
        return node

    def add_nodes_to_hosts(self, remote, nodes):
        for node in nodes:
            add_to_hosts(remote,
                         node.get_ip_address_by_network_name('internal'), node.name,
                         node.name + '.your-domain-name.com')

    def setup_master_node(self, master_remote, nodes):
        setup_puppet_master(master_remote)
        add_nmap(master_remote)
        switch_off_ip_tables(master_remote)
        self.add_nodes_to_hosts(master_remote, nodes)

    def setup_agent_nodes(self, nodes):
        agent_config = load(
            root('fuel_test', 'config', 'puppet.agent.config'))
        for node in nodes:
            if node.name != 'master':
                remote = node.remote('public', login='root',
                                     password='r00tme')
                self.add_nodes_to_hosts(remote, self.environment().nodes)
                setup_puppet_client(remote)
                write_config(remote, '/etc/puppet/puppet.conf', agent_config)
                request_cerificate(remote)

    def rename_nodes(self, nodes):
        for node in nodes:
            remote = node.remote('public', login='root', password='r00tme')
            change_host_name(remote, node.name,
                             node.name + '.your-domain-name.com')
            logging.info("Renamed %s" % node.name)

    @abstractmethod
    def setup_environment(self):
        """
        :rtype : None
        """
        pass

    def internal_virtual_ip(self):
        return str(IPNetwork(
            self.environment().network_by_name('internal').ip_network)[-2])

    def floating_network(self):
        return str(
            IPNetwork(self.environment().network_by_name('public').ip_network).subnet(new_prefix=29)[-1])

    def public_virtual_ip(self):
        return str(
            IPNetwork(self.environment().network_by_name('public').ip_network).subnet(new_prefix=29)[-2][
                -1])

    def public_router(self):
        return str(
            IPNetwork(
                self.environment().network_by_name('public').ip_network)[1])

    def internal_router(self):
        return str(
            IPNetwork(
                self.environment().network_by_name('internal').ip_network)[1])

    def fixed_network(self):
        return str(
            IPNetwork(self.environment().network_by_name('private').ip_network).subnet(
                new_prefix=27)[0])

    def internal_network(self):
        return str(IPNetwork(self.environment().network_by_name('internal').ip_network))

    def internal_net_mask(self):
        return str(IPNetwork(self.environment().network_by_name('internal').ip_network).netmask)

    def public_net_mask(self):
        return str(IPNetwork(self.environment().network_by_name('public').ip_network).netmask)

    def public_network(self):
        return str(IPNetwork(self.environment().network_by_name('public').ip_network))