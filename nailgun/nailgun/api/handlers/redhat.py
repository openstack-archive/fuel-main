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

import web
import subprocess
import shlex
import traceback

from nailgun.api.handlers.base import JSONHandler, content_json
from nailgun.api.handlers.tasks import TaskHandler
from nailgun.api.validators.redhat import RedHatAcountValidator
from nailgun.db import db
from nailgun.errors import errors
from nailgun.task.helpers import TaskHelper
from nailgun.task.manager import DownloadReleaseTaskManager
from nailgun.api.models import RedHatAccount
from nailgun.logger import logger
from nailgun.settings import settings


class RedHatAccountHandler(JSONHandler):
    fields = (
        'username',
        'password',
        'license_type',
        'satellite',
        'activation_key'
    )

    model = RedHatAccount

    validator = RedHatAcountValidator

    def check_credentials(self, data):
        if settings.FAKE_TASKS:
            if data["username"] != "rheltest":
                raise web.badrequest("Invalid username or password")
            return
        try:
            logger.info("Testing RH credentials with user %s",
                        data.username)

            cmd = 'subscription-manager orgs --username ' + \
                  '"%s" --password "%s"' % \
                  (data.get("username"), data.get("password"))

            proc = subprocess.Popen(
                shlex.split(cmd),
                shell=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)

            p_stdout, p_stderr = proc.communicate()
            logger.info(
                "'{0}' executed, STDOUT: '{1}',"
                " STDERR: '{2}'".format(cmd, p_stdout, p_stderr))

        except OSError:
            logger.warning(
                "'{0}' returned non-zero exit code".format(cmd))

            raise web.badrequest(str(p_stderr))
        except ValueError:
            error_msg = "Not valid parameters: '{0}'".format(cmd)
            logger.warning(error_msg)
            raise web.badrequest(error_msg)

    @content_json
    def GET(self):
        account = db().query(RedHatAccount).first()
        if not account:
            raise web.notfound()
        return self.render(account)

    @content_json
    def POST(self):
        data = self.checked_data()
        self.check_credentials(data)

        release_data = {'release_id': data['release_id']}
        data.pop('release_id')
        release_data['redhat'] = data

        account = db().query(RedHatAccount).first()
        if account:
            db().query(RedHatAccount).update(data)
        else:
            account = RedHatAccount(**data)
            db().add(account)
        db().commit()

        task_manager = DownloadReleaseTaskManager(release_data)
        try:
            task = task_manager.execute()
        except Exception as exc:
            logger.error(u'DownloadReleaseHandler: error while execution'
                         ' deploy task: {0}'.format(str(exc)))
            logger.error(traceback.format_exc())
            raise web.badrequest(str(exc))
        return TaskHandler.render(task)
