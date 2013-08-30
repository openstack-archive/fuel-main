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

from mock import patch

import nailgun
from nailgun.api.handlers.redhat import RedHatSetupHandler
from nailgun.api.models import RedHatAccount
from nailgun.api.models import Task
from nailgun.task.manager import RedHatSetupTaskManager
from nailgun.test.base import BaseHandlers
from nailgun.test.base import fake_tasks
from nailgun.test.base import reverse


class TestHandlers(BaseHandlers):
    def setUp(self):
        super(TestHandlers, self).setUp()
        self.release = self.env.create_release(api=False)

    @fake_tasks(fake_rpc=False, mock_rpc=False)
    @patch('nailgun.rpc.cast')
    def test_redhat_setup_task_manager(self, mocked_rpc):
        test_release_data = {
            'release_id': self.release.id,
            'redhat': {
                'license_type': 'rhsm',
                'username': 'rheltest',
                'password': 'password'
            }
        }
        rhm = RedHatSetupTaskManager(test_release_data)
        rhm.execute()

        args, kwargs = nailgun.task.manager.rpc.cast.call_args
        rpc_message = args[1]

        for i, name in enumerate((
            'check_redhat_credentials',
            'check_redhat_licenses',
            'download_release'
        )):
            self.assertEquals(rpc_message[i]['method'], name)
            self.assertEquals(
                rpc_message[i]['args']['release_info'],
                test_release_data
            )

    @fake_tasks()
    def test_redhat_account_invalid_data_handler(self):
        resp = self.app.post(
            reverse('RedHatSetupHandler'),
            json.dumps({'username': 'rheltest',
                        'password': 'password'}),
            headers=self.default_headers,
            expect_errors=True)
        self.assertEquals(resp.status, 400)

    @fake_tasks()
    def test_redhat_account_validation_success(self):
        resp = self.app.post(
            reverse('RedHatSetupHandler'),
            json.dumps({'license_type': 'rhsm',
                        'username': 'rheltest',
                        'password': 'password',
                        'release_id': self.release.id}),
            headers=self.default_headers)
        self.assertEquals(resp.status, 202)

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

    @fake_tasks()
    def test_redhat_account_get(self):
        resp = self.app.get(
            reverse('RedHatAccountHandler'),
            expect_errors=True)
        self.assertEquals(resp.status, 404)

        resp = self.app.post(
            reverse('RedHatAccountHandler'),
            json.dumps({'license_type': 'rhsm',
                        'username': 'rheltest',
                        'password': 'password',
                        'release_id': self.release.id}),
            headers=self.default_headers)
        self.assertEquals(resp.status, 200)

        resp = self.app.get(
            reverse('RedHatAccountHandler'),
            expect_errors=True)
        self.assertEquals(resp.status, 200)

        response = json.loads(resp.body)

        self.assertTrue(
            all(k in response for k in RedHatSetupHandler.fields))

    @fake_tasks()
    def test_redhat_account_update(self):
        for i in xrange(2):
            resp = self.app.post(
                reverse('RedHatAccountHandler'),
                json.dumps({'license_type': 'rhsm',
                            'username': 'rheltest',
                            'password': 'password',
                            'release_id': self.release.id}),
                headers=self.default_headers)
            self.assertEquals(resp.status, 200)
            query = self.env.db.query(RedHatAccount)
            self.assertEquals(query.count(), 1)
        self.assertEquals(query.filter_by(username='rheltest').count(), 1)
