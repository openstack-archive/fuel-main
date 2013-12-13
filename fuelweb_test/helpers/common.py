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

import urllib
import hashlib
import os.path


from glanceclient.v1 import Client as glanceclient
from keystoneclient.v2_0 import Client as keystoneclient
from novaclient.v1_1 import Client as novaclient
from fuelweb_test import settings

LOGGER = logging.getLogger(__name__)
LOGWRAP = debug(LOGGER)


class Common:
    """
    :param controller_ip:
    """
    def __init__(self, controller_ip):
        self.controller_ip = controller_ip

    def _get_auth_url(self):
        LOGGER.debug('Slave-01 is {0}'.format(self.controller_ip))
        return 'http://{0}:5000/v2.0/'.format(self.controller_ip)

    def check_image(self, url, image, md5,
                    path=settings.SERVTEST_LOCAL_PATH):
        download_url = "{0}/{1}".format(url, image)
        local_path = "{0}/{1}".format(path, image)
        LOGGER.debug('Check md5 {0} of image {1}/{2}'.format(md5, path, image))
        if not os.path.isfile(local_path):
            urllib.urlretrieve(download_url, local_path)
        with open(local_path, mode='rb') as fimage:
            digits = hashlib.md5()
            while True:
                buf = fimage.read(4096)
                if not buf:
                    break
                digits.update(buf)
            md5_local = digits.hexdigest()
        if md5_local != md5:
            LOGGER.debug('MD5 is not correct, download {0} to {1}'.format(
                         download_url, local_path))
            urllib.urlretrieve(download_url, local_path)
        return True

    def goodbye_security(self):
        auth_url = self._get_auth_url()
        nova = novaclient(username=settings.SERVTEST_USERNAME,
                          api_key=settings.SERVTEST_PASSWORD,
                          project_id=settings.SERVTEST_TENANT,
                          auth_url=auth_url)
        LOGGER.debug('Permit all TCP and ICMP in security group default')
        secgroup = nova.security_groups.find(name='default')
        nova.security_group_rules.create(secgroup.id,
                                         ip_protocol='tcp',
                                         from_port=1,
                                         to_port=65535)
        nova.security_group_rules.create(secgroup.id,
                                         ip_protocol='icmp',
                                         from_port=-1,
                                         to_port=-1)

    def image_import(self, properties, local_path, image, image_name):
        LOGGER.debug('Import image {0}/{1} to glance'.
                     format(local_path, image))
        auth_url = self._get_auth_url()
        LOGGER.debug('Auth URL is {0}'.format(auth_url))
        keystone = keystoneclient(username=settings.SERVTEST_USERNAME,
                                  password=settings.SERVTEST_PASSWORD,
                                  tenant_name=settings.SERVTEST_TENANT,
                                  auth_url=auth_url)
        token = keystone.auth_token
        LOGGER.debug('Token is {0}'.format(token))
        glance_endpoint = keystone.service_catalog.url_for(
            service_type='image', endpoint_type='publicURL')
        LOGGER.debug('Glance endpoind is {0}'.format(glance_endpoint))
        glance = glanceclient(endpoint=glance_endpoint, token=token)
        with open('{0}/{1}'.format(local_path, image)) as fimage:
            glance.images.create(name=image_name, is_public=True,
                                 disk_format='qcow2',
                                 container_format='bare', data=fimage,
                                 properties=properties)
