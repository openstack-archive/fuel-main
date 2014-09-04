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

import time

from fuelweb_test import logger as LOGGER
from fuelweb_test import logwrap as LOGWRAP


from cinderclient import client as cinderclient
from glanceclient.v1 import Client as glanceclient
from keystoneclient.v2_0 import Client as keystoneclient
from novaclient.v1_1 import Client as novaclient
import neutronclient.v2_0.client as neutronclient
from proboscis.asserts import assert_equal


class Common(object):

    def __init__(self, controller_ip, user, password, tenant):
        self.controller_ip = controller_ip
        auth_url = 'http://{0}:5000/v2.0/'.format(self.controller_ip)
        LOGGER.debug('Auth URL is {0}'.format(auth_url))
        self.nova = novaclient(username=user,
                               api_key=password,
                               project_id=tenant,
                               auth_url=auth_url)
        self.keystone = keystoneclient(username=user,
                                       password=password,
                                       tenant_name=tenant,
                                       auth_url=auth_url)
        self.cinder = cinderclient.Client(1, user, password,
                                          tenant, auth_url)
        self.neutron = neutronclient.Client(
            username=user,
            password=password,
            tenant_name=tenant,
            auth_url=auth_url)
        token = self.keystone.auth_token
        LOGGER.debug('Token is {0}'.format(token))
        glance_endpoint = self.keystone.service_catalog.url_for(
            service_type='image', endpoint_type='publicURL')
        LOGGER.debug('Glance endpoind is {0}'.format(glance_endpoint))
        self.glance = glanceclient(endpoint=glance_endpoint, token=token)

    def goodbye_security(self):
        secgroup_list = self.nova.security_groups.list()
        LOGGER.debug("Security list is {0}".format(secgroup_list))
        secgroup_id = [i.id for i in secgroup_list if i.name == 'default'][0]
        LOGGER.debug("Id of security group default is {0}".format(
            secgroup_id))
        LOGGER.debug('Permit all TCP and ICMP in security group default')
        self.nova.security_group_rules.create(secgroup_id,
                                              ip_protocol='tcp',
                                              from_port=1,
                                              to_port=65535)
        self.nova.security_group_rules.create(secgroup_id,
                                              ip_protocol='icmp',
                                              from_port=-1,
                                              to_port=-1)

    def image_import(self, local_path, image, image_name, properties=None):
        LOGGER.debug('Import image {0}/{1} to glance'.
                     format(local_path, image))
        with open('{0}/{1}'.format(local_path, image)) as fimage:
            LOGGER.debug('Try to open image')
            self.glance.images.create(
                name=image_name, is_public=True,
                disk_format='qcow2',
                container_format='bare', data=fimage,
                properties=properties)

    def create_key(self, key_name):
        LOGGER.debug('Try to create key {0}'.format(key_name))
        self.nova.keypairs.create(key_name)

    def create_instance(self, flavor_name='test_flavor', ram=64, vcpus=1,
                        disk=1, server_name='test_instance', image_name=None,
                        neutron_network=False):
        LOGGER.debug('Try to create instance')

        start_time = time.time()
        while time.time() - start_time < 100:
            try:
                if image_name:
                    image = [i.id for i in self.nova.images.list()
                             if i.name == image_name]
                else:
                    image = [i.id for i in self.nova.images.list()]
                break
            except:
                pass
        else:
            raise Exception('Can not get image')

        kwargs = {}
        if neutron_network:
            network = self.nova.networks.find(label='net04')
            kwargs['nics'] = [{'net-id': network.id, 'v4-fixed-ip': ''}]

        LOGGER.info('image uuid is {0}'.format(image))
        flavor = self.nova.flavors.create(
            name=flavor_name, ram=ram, vcpus=vcpus, disk=disk)
        LOGGER.info('flavor is {0}'.format(flavor.name))
        server = self.nova.servers.create(
            name=server_name, image=image[0], flavor=flavor, **kwargs)
        LOGGER.info('server is {0}'.format(server.name))
        return server

    @LOGWRAP
    def get_instance_detail(self, server):
        details = self.nova.servers.get(server)
        return details

    def verify_instance_status(self, server, expected_state):
        def _verify_instance_state():
            curr_state = self.get_instance_detail(server).status
            assert_equal(expected_state, curr_state)

        try:
            _verify_instance_state()
        except AssertionError:
            LOGGER.debug('Instance is not active, '
                         'lets provide it the last chance and sleep 60 sec')
            time.sleep(60)
            _verify_instance_state()

    def delete_instance(self, server):
        LOGGER.debug('Try to create instance')
        self.nova.servers.delete(server)
