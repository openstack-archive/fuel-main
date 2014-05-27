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

import requests
import jinja2
import keystoneclient.v2_0.client as keystoneclient
import neutronclient.v2_0.client as neutronclient
import glanceclient.v2.client as glanceclient

#from fuelweb_test import nailgun_client

AUTH_URL_TEMPLATE = 'http://{0}:5000/v2.0'
GLANCE_ENDPOINT = 'http://{0}:9292'


class OClient(object):

    def __init__(self, user, passw, tenant, endpoint_ip):
        self.user = user
        self.passw = passw
        self.tenant = tenant
        self.auth_url = AUTH_URL_TEMPLATE.format(endpoint_ip)
        self.glance_endpoint = GLANCE_ENDPOINT.format(endpoint_ip)
        self.token = None
        self._keystone = None
        self._neutron = None
        self._glance = None

    @property
    def keystone(self):
        if self._keystone is None:
            self._keystone = keystoneclient.Client(
                username=self.user,
                password=self.passw,
                tenant_name=self.tenant,
                auth_url=self.auth_url)
        return self._keystone

    @property
    def neutron(self):
        if self._neutron is None:
            self._neutron = neutronclient.Client(
                username=self.user,
                password=self.passw,
                tenant_name=self.tenant,
                auth_url=self.auth_url)
        return self._neutron

    def renew_token(self):
        return self.keystone.tokens.authenticate(
            username=self.user,
            password=self.passw,
            tenant_name=self.tenant)

    @property
    def glance(self):
        if self._glance is None:
            self.renew_token()
            self._glance = glanceclient.Client(
                self.glance_endpoint, self.token)
        return self._glance

    def create_tenant(self, tenant_name):
        return self.keystone.tenants.create(enabled=True,
                                            tenant_name=tenant_name)

    def create_user(self, user, passw, tenant):
        return self.keystone.users.create(
            name=user, password=passw, tenant=tenant)

    def get_network(self, network_name):
        net_list = self.neutron.list_networks()
        return next((net for net in net_list['networks']
                    if net['name'] == network_name))

    def get_router(self, network):
        router_list = self.neutron.list_routers()
        for router in router_list:
            network_id = router['external_gateway_info'].get('network_id')
            if network_id == network['id']:
                return router
        return None

    def get_image(self, image_name):
        image_list = self.glance.images.list()
        return next((img for img in image_list if img['name'] == image_name))


# TODO swap it with existing one
class NailgunClient(object):

    def __init__(self, nailgun_uri, cluster_id):
        self.nailgun_uri = nailgun_uri
        self.cluster_id = cluster_id

    def get_cluster_info(self):
        return requests.get(self.nailgun_uri+'/api/clusters/'+self.cluster_id).json()

    def get_neutron_info(self):
        return requests.get(self.nailgun_uri+
            '/api/clusters/{0}/network_configuration/{1}'.format(self.cluster_id, self.options['net_provider'])).json()

    def get_attrs_info(self):
        return requests.get(self.nailgun_uri+
            '/api/clusters/{0}/attributes/'.format(self.cluster_id)).json()


class TempestConfigState(object):

    default_options = {'username': 'test',
                       'password': 'test',
                       'tenant_name': 'test',
                       'public_network_name': 'net04_ext',
                       'image_name': 'TestVM'}

    def __init__(self, nailgun_uri, cluster_id, tempest_template=None,
                 tempest_conf=None, **kwargs):
        """WARNING!!!
        kwargs would be directly provided to templates and may be used inside configuration
        """
        self.nailgun_client = NailgunClient(nailgun_uri, cluster_id)
        self.tempest_template = tempest_template or 'tempest.conf.template'
        self.tempest_conf = tempest_conf or '/etc/tempest.conf'
        self.options = {}
        self.options.update(self.default_options)
        self.options.update(kwargs)

    def configure_nailgun(self):
        """Should be used for configuration that can be
           gathered from nailgun api, e.g:
           1. admin username, password, tenant_name
           2. management_vip/public_vip
           3. private network cidr
        """

        cluster_info = self.nailgun_client.get_cluster_info()
        self.options['net_provider'] = cluster_info['net_provider']
        self._configure_nailgun_access()
        self._configure_nailgun_network()
        if self.options['net_provider'] == 'neutron':
            self._configure_nailgun_neutron()
        else:
            self._confugure_nailgun_nova()

    def _configure_nailgun_access(self):
        cluster_attrs = self.nailgun_client.get_attrs_info()
        self.options['admin_username'] = cluster_attrs['editable']['access']['user']['value']
        self.options['admin_tenant_name'] = cluster_attrs['editable']['access']['tenant']['value']
        self.options['admin_password'] = cluster_attrs['editable']['access']['password']['value']

    def _configure_nailgun_neutron(self):
        network_attrs = self.nailgun_client.get_neutron_info()
        self.options['internal_cidr'] = network_attrs['internal_cidr']
        _, self.options['internal_mask'] = network_attrs['internal_cidr'].split('/')

    def _configure_nailgun_nova(self):
        pass

    def configure_openstack(self):
        """
        1. Fetch id of TestVM image
        2. Fetch id of neutron public network and public router
        3. Create non-admin user for keystone
        """
        client = OClient(self.options['admin_username'],
                         self.options['admin_password'],
                         self.options['admin_tenant'],
                         self.options['management_ip'])
        try:
            tenant = client.create_tenant(self.options['tenant_name'])
            client.create_user(
                self.options['username'], self.options['passwprd'],
                tenant)
        except Exception:
            # TODO check if such user is alredy exists
            pass
        network = self.client.get_network(
            self.options['public_network_name'])
        router = self.client.get_router(network)
        self.options['public_network'] = network['id']
        self.options['public_router'] = router['id']
        test_image = self.client.get_image(self.options['image_name'])
        self.options['image_ref'] = test_image['id']

    def configure(self):
        self.configure_nailgun()
        self.configure_openstack()

    def copy_config(self):
        with open(self.tempest_template, 'r') as template:
            j_template = jinja2.Template(template.read()).render(self.options)
            with open(self.tempest_conf, 'wb') as conf:
                conf.write(j_template)


if __name__ == '__main__':
    nailgun_uri = 'http://10.108.10.2:8000'
    conf = TempestConfigState(nailgun_uri)
    conf.configure()
    conf.copy_config()
