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

from nailgun.api.handlers.base import JSONHandler, content_json
from nailgun.api.handlers.tasks import TaskHandler
from nailgun.api.validators.redhat import RedHatAcountValidator
from nailgun.task.helpers import TaskHelper
from nailgun.task.manager import DownloadReleaseTaskManager
from nailgun.logger import logger


class RedHatAccountHandler(JSONHandler):
    fields = (
        "id",
        "name",
    )

    validator = RedHatAcountValidator

    @content_json
    def POST(self):
        data = self.checked_data()
        # TODO: activate and save status
        task_manager = DownloadReleaseTaskManager(data['release_id'])
        try:
            task = task_manager.execute()
        except Exception as exc:
            logger.warn(u'DownloadReleaseHandler: error while execution'
                        ' deploy task: {0}'.format(str(exc)))
            raise web.badrequest(str(exc))
        return TaskHandler.render(task)
