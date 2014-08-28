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

import traceback

from proboscis import asserts

from fuelweb_test import logger
from fuelweb_test import logwrap


@logwrap
def get_yaml_to_json(node_ssh, file):
    cmd = ("python -c 'import sys, yaml, json; json.dump("
           "yaml.load(sys.stdin),"
           " sys.stdout)' < {0}").format(file)
    err_res = ''
    try:
        res = node_ssh.execute(cmd)
        logger.debug('type of res is{0}'.format(res['stdout']))
        err_res.join(res['stderr'])
        return res['stdout']
    except:
        logger.debug("can not read file {0}. "
                     "Next result received {1}").format(file, err_res)
        logger.error(traceback.format_exc())


@logwrap
def nova_service_get_pid(node_ssh, nova_services=None):
    pid_dict = {}
    for el in nova_services:
        cmd = "ps uax| grep %s | awk -F' ' '{print $2}'" % el
        pid_dict[el] = node_ssh.execute(cmd)['stdout']
        logger.debug('current dict is {0}'. format(pid_dict))
    return pid_dict


@logwrap
def check_if_service_restarted_ubuntu(node_ssh, services_list=None):
    if services_list:
        cmd = ("grep '/sbin/restart' /var/log/puppet.log"
               "  | awk -F' ' '{print $11}' ")
        res = ''.join(node_ssh.execute(cmd)['stdout'])
        logger.debug('Next services were restarted {0}'.format(res))
        for el in services_list:
            asserts.assert_true(
                el in res,
                'Seems service {0} was not restarted {1}'.format(el, res))


@logwrap
def check_if_service_restarted_centos(node_ssh, services_list=None):
    if services_list:
        cmd_template = ("grep '/sbin/service openstack-%s'"
                        " /var/log/puppet.log| awk -F' ' '{print $11}' ")
        for service in services_list:
            res = node_ssh.execute(cmd_template % service)['stdout']
            logger.debug('Next services were restarted {0}'.format(res))
            asserts.assert_true(len(res) > 1,
                                'Seems service {0} was not restarted'
                                ' {1}'.format(service, res))
