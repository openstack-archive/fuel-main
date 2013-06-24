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


import os
import time
import logging
from devops.helpers.helpers import wait
from ipaddr import IPNetwork
from fuelweb_test.integration.ci_base import CiBase
from fuelweb_test.node_roles import NodeRoles
from fuelweb_test.settings import INTERFACE_ORDER, POOLS, EMPTY_SNAPSHOT,\
    ISO_PATH, FORWARDING, DHCP

logger = logging.getLogger('integration')


class CiFuelWeb(CiBase):
    hostname = 'nailgun'
    domain = 'mirantis.com'
    installation_timeout = 1800
    deployment_timeout = 1800
    puppet_timeout = 1000

    def node_roles(self):
        return NodeRoles(
            admin_names=['admin'],
            other_names=['slave-%02d' % x for x in range(1, 10)]
        )

    def env_name(self):
        return os.environ.get('ENV_NAME', 'fuelweb')

    def describe_environment(self):
        """
        :rtype : Environment
        """
        environment = self.manager.environment_create(self.env_name())
        networks = []
        for name in INTERFACE_ORDER:
            ip_networks = [IPNetwork(x) for x in POOLS.get(name)[0].split(',')]
            new_prefix = int(POOLS.get(name)[1])
            pool = self.manager.create_network_pool(
                networks=ip_networks, prefix=int(new_prefix))
            networks.append(self.manager.network_create(
                name=name, environment=environment, pool=pool,
                forward=FORWARDING.get(name), has_dhcp_server=DHCP.get(name)))

        for name in self.node_roles().admin_names:
            self.describe_admin_node(name, networks)
        for name in self.node_roles().other_names:
            self.describe_empty_node(name, networks, memory=1024)
        return environment

    def wait_bootstrap(self):
        logging.info("Waiting while bootstrapping is in progress")
        log_path = "/var/log/puppet/bootstrap_admin_node.log"
        wait(
            lambda: not
            self.nodes().admin.remote('internal', 'root', 'r00tme').execute(
                "grep 'Finished catalog run' '%s'" % log_path
            )['exit_code'],
            timeout=self.puppet_timeout
        )

    def get_keys(self, node):
        params = {
            'ip': node.get_ip_address_by_network_name('internal'),
            'mask': self.internal_net_mask(),
            'gw': self.internal_router(),
            'hostname': '.'.join((self.hostname, self.domain))
        }
        keys = (
            "<Esc><Enter>\n"
            "<Wait>\n"
            "vmlinuz initrd=initrd.img ks=cdrom:/ks.cfg\n"
            " ip=%(ip)s\n"
            " netmask=%(mask)s\n"
            " gw=%(gw)s\n"
            " dns1=%(gw)s\n"
            " hostname=%(hostname)s\n"
            " <Enter>\n"
        ) % params
        return keys

    def setup_environment(self):
        admin = self.nodes().admin
        admin.disk_devices.get(device='cdrom').volume.upload(ISO_PATH)
        self.environment().start(self.nodes().admins)
        time.sleep(20)
        admin.send_keys(self.get_keys(admin))
        admin.await('internal', timeout=10 * 60)
        self.wait_bootstrap()
        time.sleep(10)
        self.environment().snapshot(EMPTY_SNAPSHOT)
