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
        logger.debug('res of yaml converting is {0}'.format(res))
        logger.debug('type of res is{0}'.format(res['stdout']))
        err_res.join(res['stderr'])
        return res['stdout']
    except:
        logger.debug("can not read file {0}. "
                     "Next result received {1}").format(file, err_res)
        logger.error(traceback.format_exc())


@logwrap
def check_if_service_restarted(node_ssh, services_list=[]):
    if services_list:
        for el in services_list:
            if 'nova' not in el:
                res = node_ssh.execute(
                    'grep "openstack-{0} restart" '
                    '/var/log/puppet.log'.format(el))
                logger.debug(res['stdout'])
                asserts.assert_equal(res['exit_code'], 0, res['stderr'])
            else:
                res = node_ssh.execute(
                    'grep "{0} start" /var/log/puppet.log'.format(el))
                logger.debug(res['stdout'])
                asserts.assert_true(len(res['stdout'].split('/n')) >= 2,
                                    res['stdout'])
