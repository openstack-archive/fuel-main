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

import logging
from proboscis.asserts import assert_true, assert_false, assert_equal
from fuelweb_test.helpers.decorators import debug
from time import sleep

logger = logging.getLogger(__name__)
logwrap = debug(logger)


@logwrap
def check_ceph_health(ssh):
    # Check Ceph node disk configuration:
    disks = ''.join(ssh.execute(
        'ceph osd tree | grep osd')['stdout'])
    logger.debug("Disks output information: \\n{}".format(disks))
    assert_true('up' in disks, "Some disks are not 'up'")

    result = ''.join(ssh.execute('ceph health')['stdout'])
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


@logwrap
def verify_murano_service(remote):
    ps_output = remote.execute('ps ax')['stdout']

    murano_api = filter(lambda x: 'murano-api' in x, ps_output)
    logger.debug("murano-api \\n: {}".format(str(murano_api)))
    assert_equal(len(murano_api), 1, "murano-api count not equal to 1")

    muranoconductor = filter(lambda x: 'muranoconductor' in x, ps_output)
    logger.debug("muranoconductor \\n: {}".format(str(murano_api)))
    assert_equal(len(muranoconductor), 1,
                 "muranoconductor count not equal to 1")


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
def verify_savanna_service(remote):
    ps_output = remote.execute('ps ax')['stdout']

    savanna_api = filter(lambda x: 'savanna-api' in x, ps_output)
    logger.debug("savanna-api \\n: {}".format(str(savanna_api)))
    assert_equal(len(savanna_api), 1, "savanna-api count not equal to 1")


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
        logger.debug("Services still not read. Sleeping for 60 seconds and retrying")
        sleep(60)
        _verify()
