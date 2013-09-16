#    Copyright 2013 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


from abc import abstractproperty, abstractmethod
from devops.helpers.helpers import _get_file_size
from devops.manager import Manager
from ipaddr import IPNetwork
import hashlib
from fuelweb_test.node_roles import Nodes
from fuelweb_test.settings import EMPTY_SNAPSHOT, ISO_PATH


class CiBase(object):
    def __init__(self):
        self.manager = Manager()
        self._environment = None
        self.saved_environment_states = {}

    def _get_or_create(self):
        try:
            return self.manager.environment_get(self.env_name())
        except:
            self._environment = self.describe_environment()
            self._environment.define()
            return self._environment

    def get_state(self, name):
        if self.environment().has_snapshot(name):
            self.environment().revert(name)
            return True
        return False

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
            node, name + '-iso', capacity=_get_file_size(ISO_PATH),
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

    def get_empty_environment(self):
        if not(self.get_state(EMPTY_SNAPSHOT)):
            self.setup_environment()

    def generate_state_hash(self, settings):
        return hashlib.md5(str(settings)).hexdigest()

    def revert_to_state(self, settings):
        state_hash = self.generate_state_hash(settings)

        empty_state_hash = self.generate_state_hash({})
        if state_hash == empty_state_hash:
            # revert to empty state
            self.get_empty_environment()
            return True

        if state_hash in self.saved_environment_states:
            # revert to matching state
            state = self.saved_environment_states[state_hash]
            if not(self.get_state(state['snapshot_name'])):
                return False
            self.environment().resume()
            return True

        return False

    def snapshot_state(self, name, settings):
        state_hash = self.generate_state_hash(settings)
        snapshot_name = '{0}_{1}'.format(
            name.replace(' ', '_')[:17], state_hash)
        self.environment().suspend(verbose=False)
        self.environment().snapshot(
            name=snapshot_name,
            description=name,
            force=True,
        )
        self.environment().resume(verbose=False)
        self.saved_environment_states[state_hash] = {
            'snapshot_name': snapshot_name,
            'cluster_name': name,
            'settings': settings
        }

    def internal_virtual_ip(self):
        return str(IPNetwork(
            self.environment().network_by_name('internal').ip_network)[-2])

    def public_router(self):
        return str(
            IPNetwork(
                self.environment().network_by_name('public').ip_network)[1])

    def internal_router(self):
        return self._router('internal')

    def nat_router(self):
        return self._router('nat')

    def _router(self, router_name):
        return str(
            IPNetwork(
                self.environment().network_by_name(router_name).ip_network)[1])

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
