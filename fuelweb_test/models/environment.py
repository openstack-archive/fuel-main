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

import time

from devops.helpers.helpers import _get_file_size
from devops.helpers.helpers import SSHClient
from devops.helpers.helpers import wait
from devops.manager import Manager
from ipaddr import IPNetwork
from paramiko import RSAKey

from fuelweb_test.helpers import checkers
from fuelweb_test.helpers.decorators import revert_info
from fuelweb_test.helpers.eb_tables import Ebtables
from fuelweb_test.models.fuel_web_client import FuelWebClient
from fuelweb_test import settings
from fuelweb_test import logwrap
from fuelweb_test import logger


class EnvironmentModel(object):
    hostname = 'nailgun'
    domain = 'test.domain.local'
    installation_timeout = 1800
    deployment_timeout = 1800
    puppet_timeout = 1000
    nat_interface = ''  # INTERFACES.get('admin')
    admin_net = 'admin'

    def __init__(self, os_image=None):
        self._virtual_environment = None
        self._keys = None
        self.manager = Manager()
        self.os_image = os_image
        self._fuel_web = FuelWebClient(self.get_admin_node_ip(), self)

    def _get_or_create(self):
        try:
            return self.manager.environment_get(self.env_name)
        except Exception:
            self._virtual_environment = self.describe_environment()
            self._virtual_environment.define()
            return self._virtual_environment

    def router(self, router_name=None):
        router_name = router_name or self.admin_net
        return str(
            IPNetwork(
                self.get_virtual_environment().network_by_name(router_name).
                ip_network)[1])

    @property
    def fuel_web(self):
        """FuelWebClient
        :rtype: FuelWebClient
        """
        return self._fuel_web

    @property
    def node_roles(self):
        return NodeRoles(
            admin_names=['admin'],
            other_names=['slave-%02d' % x for x in range(1, int(
                settings.NODES_COUNT))]
        )

    @property
    def env_name(self):
        return settings.ENV_NAME

    def add_empty_volume(self, node, name,
                         capacity=settings.NODE_VOLUME_SIZE * 1024 * 1024
                         * 1024, device='disk', bus='virtio', format='qcow2'):
        self.manager.node_attach_volume(
            node=node,
            volume=self.manager.volume_create(
                name=name,
                capacity=capacity,
                environment=self.get_virtual_environment(),
                format=format),
            device=device,
            bus=bus)

    def add_node(self, memory, name, vcpu=1, boot=None):
        return self.manager.node_create(
            name=name,
            memory=memory,
            vcpu=vcpu,
            environment=self.get_virtual_environment(),
            boot=boot)

    @logwrap
    def add_syslog_server(self, cluster_id, port=5514):
        self.fuel_web.add_syslog_server(
            cluster_id, self.get_host_node_ip(), port)

    def bootstrap_nodes(self, devops_nodes, timeout=600):
        """Lists registered nailgun nodes
        Start vms and wait until they are registered on nailgun.
        :rtype : List of registered nailgun nodes
        """
        for node in devops_nodes:
            node.start()
        wait(lambda: all(self.nailgun_nodes(devops_nodes)), 15, timeout)

        for node in self.nailgun_nodes(devops_nodes):
            self.sync_node_time(self.get_ssh_to_remote(node["ip"]))

        return self.nailgun_nodes(devops_nodes)

    def create_interfaces(self, networks, node,
                          model=settings.INTERFACE_MODEL):
        for network in networks:
            self.manager.interface_create(network, node=node, model=model)

    def describe_environment(self):
        """Environment
        :rtype : Environment
        """
        environment = self.manager.environment_create(self.env_name)
        networks = []
        for name in settings.INTERFACE_ORDER:
            ip_networks = [
                IPNetwork(x) for x in settings.POOLS.get(name)[0].split(',')]
            new_prefix = int(settings.POOLS.get(name)[1])
            pool = self.manager.create_network_pool(networks=ip_networks,
                                                    prefix=int(new_prefix))
            networks.append(self.manager.network_create(
                name=name,
                environment=environment,
                pool=pool,
                forward=settings.FORWARDING.get(name),
                has_dhcp_server=settings.DHCP.get(name)))

        for name in self.node_roles.admin_names:
            self.describe_admin_node(name, networks)
        for name in self.node_roles.other_names:
            self.describe_empty_node(name, networks)
        return environment

    def devops_nodes_by_names(self, devops_node_names):
        return map(
            lambda name:
            self.get_virtual_environment().node_by_name(name),
            devops_node_names)

    @logwrap
    def describe_admin_node(self, name, networks):
        node = self.add_node(
            memory=settings.HARDWARE.get("admin_node_memory", 1024),
            vcpu=settings.HARDWARE.get("admin_node_cpu", 1),
            name=name,
            boot=['hd', 'cdrom'])
        self.create_interfaces(networks, node)

        if self.os_image is None:
            self.add_empty_volume(node, name + '-system')
            self.add_empty_volume(
                node,
                name + '-iso',
                capacity=_get_file_size(settings.ISO_PATH),
                format='raw',
                device='cdrom',
                bus='ide')
        else:
            volume = self.manager.volume_get_predefined(self.os_image)
            vol_child = self.manager.volume_create_child(
                name=name + '-system',
                backing_store=volume,
                environment=self.get_virtual_environment()
            )
            self.manager.node_attach_volume(
                node=node,
                volume=vol_child
            )
        return node

    def describe_empty_node(self, name, networks):
        node = self.add_node(
            name=name,
            memory=settings.HARDWARE.get("slave_node_memory", 1024),
            vcpu=settings.HARDWARE.get("slave_node_cpu", 1))
        self.create_interfaces(networks, node)
        self.add_empty_volume(node, name + '-system')

        if settings.USE_ALL_DISKS:
            self.add_empty_volume(node, name + '-cinder')
            self.add_empty_volume(node, name + '-swift')

        return node

    @logwrap
    def get_admin_remote(self):
        """SSH to admin node
        :rtype : SSHClient
        """
        return self.nodes().admin.remote(self.admin_net,
                                         login='root',
                                         password='r00tme')

    @logwrap
    def get_admin_node_ip(self):
        return str(
            self.nodes().admin.get_ip_address_by_network_name(self.admin_net))

    @logwrap
    def get_ebtables(self, cluster_id, devops_nodes):
        return Ebtables(self.get_target_devs(devops_nodes),
                        self.fuel_web.client.get_cluster_vlans(cluster_id))

    def get_host_node_ip(self):
        return self.router()

    def get_keys(self, node):
        params = {
            'ip': node.get_ip_address_by_network_name(self.admin_net),
            'mask': self.get_net_mask(self.admin_net),
            'gw': self.router(),
            'hostname': '.'.join((self.hostname, self.domain)),
            'nat_interface': self.nat_interface,
            'dns1': settings.DNS

        }
        keys = (
            "<Esc><Enter>\n"
            "<Wait>\n"
            "vmlinuz initrd=initrd.img ks=cdrom:/ks.cfg\n"
            " ip=%(ip)s\n"
            " netmask=%(mask)s\n"
            " gw=%(gw)s\n"
            " dns1=%(dns1)s\n"
            " hostname=%(hostname)s\n"
            " dhcp_interface=%(nat_interface)s\n"
            " <Enter>\n"
        ) % params
        return keys

    @logwrap
    def get_private_keys(self, force=False):
        if force or self._keys is None:
            self._keys = []
            for key_string in ['/root/.ssh/id_rsa',
                               '/root/.ssh/bootstrap.rsa']:
                with self.get_admin_remote().open(key_string) as f:
                    self._keys.append(RSAKey.from_private_key(f))
        return self._keys

    @logwrap
    def get_ssh_to_remote(self, ip):
        return SSHClient(ip,
                         username='root',
                         password='r00tme',
                         private_keys=self.get_private_keys())

    @logwrap
    def get_ssh_to_remote_by_name(self, node_name):
        return self.get_ssh_to_remote(
            self.fuel_web.get_nailgun_node_by_devops_node(
                self.get_virtual_environment().node_by_name(node_name))['ip']
        )

    def get_target_devs(self, devops_nodes):
        return [
            interface.target_dev for interface in [
                val for var in map(lambda node: node.interfaces, devops_nodes)
                for val in var]]

    def get_virtual_environment(self):
        """Returns virtual environment
        :rtype : devops.models.Environment
        """
        if self._virtual_environment is None:
            self._virtual_environment = self._get_or_create()
        return self._virtual_environment

    def get_network(self, net_name):
        return str(
            IPNetwork(
                self.get_virtual_environment().network_by_name(net_name).
                ip_network))

    def get_net_mask(self, net_name):
        return str(
            IPNetwork(
                self.get_virtual_environment().network_by_name(
                    net_name).ip_network).netmask)

    def make_snapshot(self, snapshot_name, description=""):
        self.get_virtual_environment().suspend(verbose=False)
        self.get_virtual_environment().snapshot(snapshot_name, force=True)
        revert_info(snapshot_name, description)

    def nailgun_nodes(self, devops_nodes):
        return map(
            lambda node: self.fuel_web.get_nailgun_node_by_devops_node(node),
            devops_nodes
        )

    def nodes(self):
        return Nodes(self.get_virtual_environment(), self.node_roles)

    def revert_snapshot(self, name):
        if self.get_virtual_environment().has_snapshot(name):
            logger.info('We have snapshot with such name %s' % name)

            self.get_virtual_environment().revert(name)
            logger.info('Starting snapshot reverting ....')

            self.get_virtual_environment().resume()
            logger.info('Starting snapshot resuming ...')

            self.nodes().admin.await(self.admin_net, timeout=10 * 60)

            list = self.nodes().slaves
            for node in list:
                nailgun_node = self.fuel_web.get_nailgun_node_by_devops_node(
                    node)
                if not node.driver.node_active(node) or \
                        nailgun_node['status'] not in ['provisioned', 'ready']:
                    continue
                try:
                    self.sync_node_time(self.get_ssh_to_remote(
                        node.get_ip_address_by_network_name(self.admin_net)))
                except Exception as e:
                    logger.warn(
                        'Paramiko exception catched while'
                        ' trying to run ntpdate: %s' % e)
            return True
        return False

    def setup_environment(self):
        # start admin node
        admin = self.nodes().admin
        admin.disk_devices.get(device='cdrom').volume.upload(settings.ISO_PATH)
        self.get_virtual_environment().start(self.nodes().admins)
        # update network parameters at boot screen
        time.sleep(float(settings.ADMIN_NODE_SETUP_TIMEOUT))
        admin.send_keys(self.get_keys(admin))
        # wait while installation complete
        admin.await(self.admin_net, timeout=10 * 60)
        self.wait_bootstrap()
        time.sleep(10)
        self.sync_time_admin_node()

    @logwrap
    def sync_node_time(self, remote):
        remote.execute('hwclock --hctosys')
        remote.execute("ntpdate -u "
                       "$(egrep '^server' /etc/ntp.conf |"
                       " sed '/^#/d' | awk '{print $2}' |"
                       " tail -n 1)")
        remote.execute('hwclock -w')

    def sync_time_admin_node(self):
        self.sync_node_time(self.get_admin_remote())

    def verify_node_service_list(self, node_name, smiles_count):
        remote = self.get_ssh_to_remote_by_name(node_name)
        checkers.verify_service_list(remote, smiles_count)

    def verify_network_configuration(self, node_name):
        checkers.verify_network_configuration(
            node=self.fuel_web.get_nailgun_node_by_name(node_name),
            remote=self.get_ssh_to_remote_by_name(node_name)
        )

    def wait_bootstrap(self):
        logger.info("Waiting while bootstrapping is in progress")
        log_path = "/var/log/puppet/bootstrap_admin_node.log"
        wait(
            lambda: not
            self.get_admin_remote().execute(
                "grep 'Finished catalog run' '%s'" % log_path
            )['exit_code'],
            timeout=self.puppet_timeout
        )


class NodeRoles(object):
    def __init__(self,
                 admin_names=None,
                 other_names=None):
        self.admin_names = admin_names or []
        self.other_names = other_names or []


class Nodes(object):
    def __init__(self, environment, node_roles):
        self.admins = []
        self.others = []
        for node_name in node_roles.admin_names:
            self.admins.append(environment.node_by_name(node_name))
        for node_name in node_roles.other_names:
            self.others.append(environment.node_by_name(node_name))
        self.slaves = self.others
        self.all = self.slaves + self.admins
        self.admin = self.admins[0]

    def __iter__(self):
        return self.all.__iter__()
