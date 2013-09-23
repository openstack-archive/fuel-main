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

"""
Handlers dealing with exclusive Red Hat tasks
"""

import traceback

import web

from nailgun.api.handlers.base \
    import JSONHandler, content_json, build_json_response
from nailgun.api.handlers.tasks import TaskHandler
from nailgun.api.validators.redhat import RedHatAccountValidator
from nailgun.db import db
from nailgun import notifier
from nailgun.errors import errors
from nailgun.task.helpers import TaskHelper
from nailgun.task.manager import RedHatSetupTaskManager
from nailgun.api.models import RedHatAccount
from nailgun.api.models import Release
from nailgun.logger import logger
from nailgun.settings import settings


class RedHatAccountHandler(JSONHandler):
    """
    Red Hat account handler
    """

    fields = (
        'username',
        'password',
        'license_type',
        'satellite',
        'activation_key'
    )
    model = RedHatAccount

    @content_json
    def GET(self):
        """
        :returns: JSONized RedHatAccount object.
        :http: * 200 (OK)
               * 404 (account not found in db)
        """
        account = db().query(RedHatAccount).first()
        if not account:
            raise web.notfound()
        return self.render(account)

    @content_json
    def POST(self):
        """
        :returns: JSONized RedHatAccount object.
        :http: * 200 (OK)
               * 400 (invalid account data specified)
               * 404 (account not found in db)
        """
        data = self.checked_data()

        license_type = data.get("license_type")
        if license_type == 'rhsm':
            data["satellite"] = ""
            data["activation_key"] = ""

        release_id = data.pop('release_id')
        release_db = db().query(Release).get(release_id)
        if not release_db:
            raise web.notfound(
                "No release with ID={0} found".format(release_id)
            )
        account = db().query(RedHatAccount).first()
        if account:
            db().query(RedHatAccount).update(data)
        else:
            account = RedHatAccount(**data)
            db().add(account)
        db().commit()
        return self.render(account)


class RedHatSetupHandler(JSONHandler):
    """
    Red Hat setup handler
    """

    validator = RedHatAccountValidator

    @content_json
    def POST(self):
        """
        Starts Red Hat setup and download process

        :returns: JSONized Task object.
        :http: * 202 (setup task created and started)
               * 400 (invalid account data specified)
               * 404 (release not found in db)
        """
        data = self.checked_data()

        license_type = data.get("license_type")
        if license_type == 'rhsm':
            data["satellite"] = ""
            data["activation_key"] = ""

        release_data = {'release_id': data['release_id']}
        release_id = data.pop('release_id')
        release_db = db().query(Release).get(release_id)
        if not release_db:
            raise web.notfound(
                "No release with ID={0} found".format(release_id)
            )
        release_data['redhat'] = data
        release_data['release_name'] = release_db.name

        account = db().query(RedHatAccount).first()
        if account:
            db().query(RedHatAccount).update(data)
        else:
            account = RedHatAccount(**data)
            db().add(account)
        db().commit()

        task_manager = RedHatSetupTaskManager(release_data)
        try:
            task = task_manager.execute()
        except Exception as exc:
            logger.error(u'RedHatAccountHandler: error while execution'
                         ' Red Hat validation task: {0}'.format(str(exc)))
            logger.error(traceback.format_exc())
            raise web.badrequest(str(exc))

        data = build_json_response(TaskHandler.render(task))
        raise web.accepted(data=data)
