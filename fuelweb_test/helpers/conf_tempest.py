#    Copyright 2014 Mirantis, Inc.
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

import argparse
import os

import jinja2

from fuelweb_test import logger
from fuelweb_test.models import nailgun_client
from fuelweb_test.helpers import os_actions


class TempestConfigState(object):
    """TempestConfigState."""  # TODO documentation

    default_options = {'username': 'test',
                       'password': 'test',
                       'tenant_name': 'test',
                       'alt_username': 'alt_test',
                       'alt_password': 'alt_test',
                       'alt_tenant_name': 'alt_test',
                       'public_network_name': 'net04_ext',
                       'image_name': 'TestVM'}

    def __init__(self, admin_ip, cluster_id,
                 tempest_conf=None, **kwargs):
        self.cluster_id = str(cluster_id)
        self.admin_ip = admin_ip
        self.tempest_template = os.path.join(os.path.dirname(
            os.path.realpath(__file__)), 'tempest.conf.template')
        self.tempest_conf = tempest_conf
        self.options = dict(self.default_options, **kwargs)

    def configure_nailgun(self):
        """Should be used for configuration that can be
           gathered from nailgun api, e.g:
           1. admin username, password, tenant_name
           2. management_vip/public_vip
           3. private network cidr
        """
        client = nailgun_client.NailgunClient(self.admin_ip)
        cluster_info = client.get_cluster(self.cluster_id)
        self.options['net_provider'] = cluster_info['net_provider']
        self._configure_nailgun_access(client)
        self._configure_nailgun_networks(client)

    def _configure_nailgun_access(self, client):
        cluster_attrs = client.get_cluster_attributes(
            self.cluster_id)
        access = cluster_attrs['editable']['access']
        self.options['admin_username'] = access['user']['value']
        self.options['admin_tenant_name'] = access['tenant']['value']
        self.options['admin_password'] = access['password']['value']

    def _configure_nailgun_networks(self, client):
        network_attrs = client.get_networks(self.cluster_id)
        networking_params = network_attrs['networking_parameters']
        if self.options['net_provider'] == 'neutron':
            cidr = networking_params['internal_cidr']
        else:
            cidr = networking_params['fixed_networks_cidr']
        self.options['internal_cidr'] = cidr
        _, self.options['internal_mask'] = cidr.split('/')
        self.options['management_vip'] = network_attrs['management_vip']

    def configure_openstack(self):
        """
        1. Fetch id of TestVM image
        2. Fetch id of neutron public network and public router
        3. Create non-admin user for keystone
        """
        client = os_actions.OpenStackActions(
            self.options['management_vip'],
            user=self.options['admin_username'],
            passwd=self.options['admin_password'],
            tenant=self.options['admin_tenant_name'])

        self._configure_openstack_keystone(client)
        self._configure_openstack_glance(client)
        if self.options['net_provider'] == 'neutron':
            self._configure_openstack_neutron(client)
        else:
            self._configure_nova_network(client)

    def _configure_openstack_neutron(self, client):
        network = client.get_network(self.options['public_network_name'])
        router = client.get_router(network)
        self.options['public_network'] = network['id']
        self.options['public_router'] = router['id']

    def _configure_nova_network(self, client):
        pass

    def _configure_openstack_keystone(self, client):
        # Keystone should create tenant/user or return existing
        client.create_user_and_tenant(
            self.options['tenant_name'],
            self.options['username'],
            self.options['password'])
        client.create_user_and_tenant(
            self.options['alt_tenant_name'],
            self.options['alt_username'],
            self.options['alt_password'])

    def _configure_openstack_glance(self, client):
        test_image = client.get_image(self.options['image_name'])
        self.options['image_ref'] = test_image.id

    def configure(self):
        self.configure_nailgun()
        self.configure_openstack()

    def copy_config(self):
        with open(self.tempest_template, 'r') as template:
            j_template = jinja2.Template(template.read()).render(self.options)
            with open(self.tempest_conf, 'w') as conf:
                conf.write(j_template)


def main():
    parser = argparse.ArgumentParser(description="""
        Example: python helpers/conf_tempest.py -c 1 \
                -n 10.108.10.2 \
                -t /home/fuel/tempest/etc/tempest.conf
        """)
    parser.add_argument("-n", "--nailgun", help="Provide nailgun node ip.",
                        required=True)
    parser.add_argument("-c", "--cluster", help="Provide cluster id",
                        required=True)
    parser.add_argument(
        "-t", "--tempest_config",
        help="Path where tempest will look for config",
        default='/etc/tempest/tempest.conf')
    args = parser.parse_args()
    conf = TempestConfigState(
        args.nailgun, args.cluster,
        tempest_conf=args.tempest_config)
    conf.configure()
    conf.copy_config()

if __name__ == '__main__':
    logger.info('Starting tempest config generation.')
    main()
    logger.info('Finished tempest config generation.')
