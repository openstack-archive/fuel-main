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
import re
import traceback
from fuelweb_test import logger
from fuelweb_test import logwrap
from proboscis.asserts import assert_equal
from proboscis.asserts import assert_false
from proboscis.asserts import assert_true
from devops.helpers.helpers import wait

import os
from time import sleep


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
def check_image(image, md5, path):
    local_path = "{0}/{1}".format(path, image)
    logger.debug('Check md5 {0} of image {1}/{2}'.format(md5, path, image))
    if not os.path.isfile(local_path):
        logger.error('Image {0} not found in {1} directory'.format(
            image, path))
        return False
    with open(local_path, mode='rb') as fimage:
        digits = hashlib.md5()
        while True:
            buf = fimage.read(4096)
            if not buf:
                break
            digits.update(buf)
        md5_local = digits.hexdigest()
    if md5_local != md5:
        logger.error('MD5 of {0}/{1} is not correct, aborting'.format(
            path, image))
        return False
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
def get_mongo_partitions(remote, device):
    ret = remote.check_call("lsblk | grep {device} | awk {size}".format(
                            device=device,
                            size=re.escape('{print $4}')))['stdout']
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


@logwrap
def check_upgraded_containers(remote, version_from, version_to):
    containers = remote.execute("docker ps | tail -n +2 |"
                                " awk '{ print $NF;}'")['stdout']
    symlink = remote.execute("ls -l /etc/supervisord.d/ - current")['stdout']
    logger.debug('containers are {0}'.format(containers))
    logger.debug('symlinks are {0}'.format(symlink))
    components = [co.split('-') for x in containers for co in x.split(',')]

    for i in components:
        assert_true(version_from != i[2],
                    'There are {0} containers'.format(version_from))
    for i in components:
        assert_true(version_to == i[2],
                    'There are no {0} containers'.format(version_to))
    for i in range(0, len(symlink)):
        if 'current -> /etc/supervisord.d' in symlink[i]:
            assert_true('current -> /etc/supervisord.d/{0}'.format(version_to)
                        in symlink[i],
                        'Symlink is set not to {0}'.format(version_to))


@logwrap
def upload_tarball(node_ssh, tar_path, tar_target):
    try:
        logger.debug("Start to upload tar file")
        node_ssh.upload(tar_path, tar_target)
    except Exception as e:
        logger.error('Failed to upload file with error {0}'.format(e))
        logger.error(traceback.format_exc())


@logwrap
def check_tarball_exists(node_ssh, name, path):
    result = ''.join(node_ssh.execute(
        'ls -all {0} | grep {1}'.format(path, name))['stdout'])
    assert_true(name in result, 'Can not find tarball')


@logwrap
def untar(node_ssh, name, path):
    result = ''.join(node_ssh.execute(
        'cd {0} && tar -xpvf {1}'.format(path, name))['stdout'])
    logger.debug('Result from tar command is {0}'.format(result))


@logwrap
def run_script(node_ssh, script_path, script_name):
    path = os.path.join(script_path, script_name)
    c_res = node_ssh.execute('chmod 755 {0}'.format(path))
    logger.debug("Result of cmod is {0}".format(c_res))
    chan, stdin, stderr, stdout = node_ssh.execute_async(path)
    logger.debug('Try to read status code from chain...')
    logger.debug('Exit status is {0}'.format(chan.recv_exit_status()))
    #assert_equal(chan.recv_exit_status(), 0,
                 #'Upgrade script fails with next message {0}'.
                 #format(chan.recv_exit_status()))


@logwrap
def run_with_rollback(node_ssh, script_path, script_name):
    path = os.path.join(script_path, script_name)
    c_res = node_ssh.execute('chmod 755 {0}'.format(path))
    logger.debug("Result of cmod is {0}".format(c_res))
    chan, stdin, stderr, stdout = node_ssh.execute_async(path)
    logger.debug('Try to read status code from chain...')


@logwrap
def wait_upgrade_is_done(node_ssh, timeout):
    logger.debug('start waiting for upgrade done')
    logger.info('waiting for upgrade starts')
    wait(
        lambda: not node_ssh.execute(
            "grep 'upgrade is done!' /var/log/fuel_upgrade.log"
        )['exit_code'], timeout=timeout)


@logwrap
def wait_rollback_is_done(node_ssh, timeout):
    wait(
        lambda: not node_ssh.execute(
            "grep 'rollback is done!' /var/log/fuel_upgrade.log"
        )['exit_code'], timeout=timeout)
    logger.debug('rollback exit code is {0}'.format(node_ssh.execute(
                 "grep 'rollback is done!' /var/log/fuel_upgrade.log"
                 )['exit_code']))
