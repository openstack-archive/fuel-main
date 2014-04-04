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

from fuelweb_test import logger
from fuelweb_test import logwrap
from proboscis.asserts import assert_equal
from proboscis.asserts import assert_false
from proboscis.asserts import assert_true
from devops.helpers.helpers import wait

import os
from time import sleep
import urllib


@logwrap
def check_ceph_health(ssh):
    wait(
        lambda: 'HEALTH_OK' in ''.join(ssh.execute('ceph -s')['stdout']),
        interval=120,
        timeout=360)

    # Check Ceph node disk configuration:
    disks = ''.join(ssh.execute(
        'ceph osd tree | grep osd')['stdout'])
    logger.debug("Disks output information: \\n{}".format(disks))
    assert_true('up' in disks, "Some disks are not 'up'")

    result = ''.join(ssh.execute('ceph -s')['stdout'])
    assert_true('HEALTH_OK' in result,
                "Ceph status is '{}' != HEALTH_OK".format(result))


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
    logger.info("glance index output: \\n{}" .format(ret))
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
def get_ceph_partitions(remote, device, type="xfs"):
    ret = remote.check_call("parted {device} print | grep {type}".format(
                            device=device, type=type))['stdout']
    if not ret:
        logger.error("Partition not present! {partitions}: ".format(
                     remote.check_call("parted {device} print")))
        raise Exception
    logger.debug("Partitions: {part}".format(part=ret))
    return ret


@logwrap
def check_unallocated_space(disks, contr_img_ceph=False):
    for disk in disks:
        # In case we have Ceph for images all space on controller
        # should be given to Base System space:
        if contr_img_ceph:
            logger.info("Check that all space on /dev/{d} is allocated for "
                        "Base System Space".format(d=disk['name']))
            if not bool(disk["volumes"][0]["size"] == disk["size"]):
                return False
        else:
            logger.info("Get overall size of volumes")
            sizes = [v['size'] for v in disk["volumes"]]
            logger.info("Space on disk: {s}".format(s=disk['size']))
            logger.info("Summary space of disks on /dev/{d}: {s}".format(
                d=disk["name"], s=sum(sizes)))
            if not bool(sum(sizes) == disk["size"]):
                return False
    return True
