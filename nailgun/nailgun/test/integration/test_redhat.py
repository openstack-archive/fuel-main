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

import json

from nailgun.api.models import Task
from nailgun.test.base import BaseIntegrationTest
from nailgun.test.base import fake_tasks
from nailgun.test.base import reverse


class TestHandlers(BaseIntegrationTest):
    def setUp(self):
        super(TestHandlers, self).setUp()
        self.release = self.env.create_release(api=False)

    @fake_tasks()
    def test_redhat_account_validation_failure(self):
        resp = self.app.post(
            reverse('RedHatSetupHandler'),
            json.dumps({'license_type': 'rhsm',
                        'username': 'some_user',
                        'password': 'password',
                        'release_id': self.release.id}),
            headers=self.default_headers,
            expect_errors=True)
        self.assertEquals(resp.status, 202)

        supertask = self.db.query(Task).filter_by(
            name="redhat_check_credentials"
        ).first()
        self.env.wait_error(supertask)
