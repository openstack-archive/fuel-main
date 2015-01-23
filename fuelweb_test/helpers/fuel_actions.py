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

import yaml
import re

from proboscis.asserts import assert_equal

from fuelweb_test import logger


class BaseActions(object):
    def __init__(self, admin_remote):
        self.admin_remote = admin_remote
        self.container = None

    def execute_in_container(self, command, container=None, exit_code=None,
                             stdin=None):
        if not container:
            container = self.container
        cmd = 'dockerctl shell {0} {1}'.format(container, command)
        if stdin is not None:
            cmd = 'echo "{0}" | {1}'.format(stdin, cmd)
        result = self.admin_remote.execute(cmd)
        if exit_code is not None:
            assert_equal(exit_code,
                         result['exit_code'],
                         ('Command {cmd} returned exit code "{e}", but '
                          'expected "{c}". Output: {out}; {err} ').format(
                             cmd=cmd,
                             e=result['exit_code'],
                             c=exit_code,
                             out=result['stdout'],
                             err=result['stderr']
                         ))
        return ''.join(result['stdout']).strip()


class NailgunActions(BaseActions):
    def __init__(self, admin_remote):
        super(NailgunActions, self).__init__(admin_remote)
        self.container = 'nailgun'

    def update_nailgun_settings_once(self, settings):
        # temporary change Nailgun settings (until next container restart)
        cfg_file = '/etc/nailgun/settings.yaml'
        ng_settings = yaml.load(self.execute_in_container(
            'cat {0}'.format(cfg_file), exit_code=0))
        ng_settings.update(settings)
        logger.debug('Uploading new nailgun settings: {}'.format(
            ng_settings))
        self.execute_in_container('tee {0}'.format(cfg_file),
                                  stdin=yaml.dump(ng_settings),
                                  exit_code=0)

    def set_collector_address(self, host, port, ssl=False):
        cmd = ("awk '/COLLECTOR.*URL/' /usr/lib/python2.6"
               "/site-packages/nailgun/settings.yaml")
        protocol = 'http' if not ssl else 'https'
        parameters = {}
        for p in self.execute_in_container(cmd, exit_code=0).split('\n'):
            parameters[p.split(': ')[0]] = re.sub(
                r'https?://\{collector_server\}',
                '{0}://{1}:{2}'.format(protocol, host, port),
                p.split(': ')[1])[1:-1]
        logger.debug('Custom collector parameters: {0}'.format(parameters))
        self.update_nailgun_settings_once(parameters)
        if ssl:
            # if test collector server doesn't have trusted SSL cert
            # installed we have to use this hack in order to disable cert
            # verification and allow using of self-signed SSL certificate
            cmd = ("sed -i '/elf.verify/ s/True/False/' /usr/lib/python2.6"
                   "/site-packages/requests/sessions.py")
            self.execute_in_container(cmd, exit_code=0)

    def force_fuel_stats_sending(self):
        log_file = '/var/log/nailgun/statsenderd.log'
        # Rotate logs on restart in order to get rid of old errors
        cmd = 'mv {0}{{,.backup_$(date +%s)}}'.format(log_file)
        self.execute_in_container(cmd)
        cmd = 'supervisorctl restart statsenderd'
        self.execute_in_container(cmd, exit_code=0)
        cmd = 'grep -sw "ERROR" {0}'.format(log_file)
        try:
            self.execute_in_container(cmd, exit_code=1)
        except AssertionError:
            logger.error(("Fuel stats were sent with errors! Check its log"
                         "s in {0} for details.").format(log_file))
            raise


class PostgresActions(BaseActions):
    def __init__(self, admin_remote):
        super(PostgresActions, self).__init__(admin_remote)
        self.container = 'postgres'

    def run_query(self, db, query):
        cmd = "su - postgres -c 'psql -qt -d {0} -c \"{1};\"'".format(
            db, query)
        return self.execute_in_container(cmd, exit_code=0)

    def action_logs_contain(self, action, group=False,
                            table='action_logs'):
        logger.info("Checking that '{0}' action was logged..".format(
            action))
        log_filter = "action_name" if not group else "action_group"
        q = "select id from {0} where {1} = '\"'\"'{2}'\"'\"'".format(
            table, log_filter, action)
        logs = [i.strip() for i in self.run_query('nailgun', q).split('\n')
                if re.compile(r'\d+').match(i.strip())]
        logger.info("Found log records with ids: {0}".format(logs))
        return len(logs) > 0

    def count_sent_action_logs(self, table='action_logs'):
        q = "select count(id) from {0} where is_sent = True".format(table)
        return int(self.run_query('nailgun', q))
