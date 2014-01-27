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

import hashlib
import logging
import os.path
import urllib

from proboscis.asserts import assert_true, assert_false, assert_equal
from time import sleep

from fuelweb_test.helpers.decorators import debug


logger = logging.getLogger(__name__)
logwrap = debug(logger)


@logwrap
def check_ceph_health(ssh, recovery_timeout=False):
    if recovery_timeout:
        logger.debug("Timeout for ceph recovery.")
        sleep(300)

    # Check Ceph node disk configuration:
    disks = ''.join(ssh.execute(
        'ceph osd tree | grep osd')['stdout'])
    logger.debug("Disks output information: \\n{}".format(disks))
    assert_true('up' in disks, "Some disks are not 'up'")

    result = ''.join(ssh.execute('ceph -s')['stdout'])
    assert_true('HEALTH_OK' in result,
                "Ceph status is '{}' != HEALTH_OK".format(result))


@logwrap
def get_interface_description(ctrl_ssh, interface_short_name):
    return ''.join(
        ctrl_ssh.execute(
            '/sbin/ip addr show dev %s' % interface_short_name
        )['stdout']
    )


@logwrap
def verify_glance_index(remote):
    ret = remote.check_call('. /root/openrc; glance index')['stdout']
    logger.debug("glance index output: \\n{}" .format(ret))
    assert_equal(1, ''.join(ret).count("TestVM"),
                 "TestVM not found in glance index")


def verify_network_configuration(remote, node):
    for interface in node['network_data']:
        if interface.get('vlan') is None:
            continue  # todo excess check fix interface json format
        interface_name = "{}.{}@{}".format(
            interface['dev'], interface['vlan'], interface['dev'])
        interface_short_name = "{}.{}".format(
            interface['dev'], interface['vlan'])
        interface_description = get_interface_description(
            remote, interface_short_name)
        assert_true(interface_name in interface_description)
        if interface.get('name') == 'floating':
            continue
        if interface.get('ip'):
            assert_true(
                "inet {}".format(interface.get('ip')) in
                interface_description)
        else:
            assert_false("inet " in interface_description)
        if interface.get('brd'):
            assert_true(
                "brd {}".format(interface['brd']) in interface_description)


@logwrap
def verify_network_list(networks_count, remote):
    ret = remote.check_call('/usr/bin/nova-manage network list')
    logger.debug("network list: \\n: {}".format(ret['stdout']))
    assert_equal(len(ret['stdout'][1:]), networks_count,
                 "Actual network list {} not equal to expected {}".format(
                     len(ret['stdout'][1:]), networks_count))


@logwrap
def verify_service(remote, service_name):
    ps_output = remote.execute('ps ax')['stdout']
    api = filter(lambda x: service_name in x, ps_output)
    logger.debug("{} \\n: {}".format(service_name, str(api)))
    assert_equal(len(api), 1, "{} count not equal to 1".format(service_name))


@logwrap
def verify_service_list(remote, smiles_count):
    def _verify():
        ret = remote.check_call('/usr/bin/nova-manage service list')
        logger.debug("Service list: {}".format(ret['stdout']))
        assert_equal(
            smiles_count, ''.join(ret['stdout']).count(":-)"), "Smiles count")
        assert_equal(
            0, ''.join(ret['stdout']).count("XXX"), "Broken services count")

    try:
        _verify()
    except AssertionError:
        logger.debug(
            "Services still not read. Sleeping for 60 seconds and retrying")
        sleep(60)
        _verify()


@logwrap
def check_image(url, image, md5, path):
    download_url = "{0}/{1}".format(url, image)
    local_path = "{0}/{1}".format(path, image)
    logger.debug('Check md5 {0} of image {1}/{2}'.format(md5, path, image))
    if not os.path.isfile(local_path):
        try:
            urllib.urlretrieve(download_url, local_path)
        except Exception as error:
            logger.error(error)
    with open(local_path, mode='rb') as fimage:
        digits = hashlib.md5()
        while True:
            buf = fimage.read(4096)
            if not buf:
                break
            digits.update(buf)
        md5_local = digits.hexdigest()
    if md5_local != md5:
        logger.debug('MD5 is not correct, download {0} to {1}'.format(
                     download_url, local_path))
        try:
            urllib.urlretrieve(download_url, local_path)
        except Exception as error:
            logger.error(error)

    return True
