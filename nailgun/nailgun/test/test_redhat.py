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
from paste.fixture import TestApp
import shlex

import mock
from mock import patch

import nailgun
from nailgun.api.handlers.redhat import RedHatAccountHandler
from nailgun.api.models import Release
from nailgun.settings import settings


from nailgun.api.handlers.redhat import RedHatAccountHandler
from nailgun.api.models import RedHatAccount
from nailgun.test.base import BaseHandlers
from nailgun.test.base import fake_tasks
from nailgun.test.base import reverse


class TestHandlers(BaseHandlers):
    def setUp(self):
        super(TestHandlers, self).setUp()
        self.release = self.env.create_release(api=False)
        nailgun.task.task.DownloadReleaseTask.execute = mock.Mock()

    @fake_tasks()
    def test_redhat_account_handler(self):
        release = self.env.create_release(api=False)
        resp = self.app.post(
            reverse('RedHatAccountHandler'),
            json.dumps({'license_type': 'rhsm',
                        'username': 'rheltest',
                        'password': 'password',
                        'release_id': release.id}),
            headers=self.default_headers)
        self.assertEquals(resp.status, 200)

    @fake_tasks()
    def test_redhat_account_invalid_data_handler(self):
        resp = self.app.post(
            reverse('RedHatAccountHandler'),
            json.dumps({'username': 'rheltest',
                        'password': 'password'}),
            headers=self.default_headers,
            expect_errors=True)
        self.assertEquals(resp.status, 400)

    @fake_tasks()
    def test_redhat_account_validation_success(self):
        resp = self.app.post(
            reverse('RedHatAccountHandler'),
            json.dumps({'license_type': 'rhsm',
                        'username': 'rheltest',
                        'password': 'password',
                        'release_id': self.release.id}),
            headers=self.default_headers)
        self.assertEquals(resp.status, 200)

    @fake_tasks()
    def test_redhat_account_validation_failure(self):
        resp = self.app.post(
            reverse('RedHatAccountHandler'),
            json.dumps({'license_type': 'rhsm',
                        'username': 'some_user',
                        'password': 'password',
                        'release_id': self.release.id}),
            headers=self.default_headers,
            expect_errors=True)
        self.assertEquals(resp.status, 400)

    def test_redhat_account_get(self):
        resp = self.app.get(
            reverse('RedHatAccountHandler'),
            expect_errors=True)
        self.assertEquals(resp.status, 404)

        resp = self.app.post(
            reverse('RedHatAccountHandler'),
            json.dumps({'license_type': 'rhsm',
                        'username': 'user',
                        'password': 'password',
                        'release_id': 1}),
            headers=self.default_headers)
        self.assertEquals(resp.status, 200)

        resp = self.app.get(
            reverse('RedHatAccountHandler'),
            expect_errors=True)
        self.assertEquals(resp.status, 200)

        response = json.loads(resp.body)

        self.assertTrue(
            all(k in response for k in RedHatAccountHandler.fields))

    def test_redhat_account_update(self):
        for i in xrange(2):
            username = 'user{0}'.format(i)
            resp = self.app.post(
                reverse('RedHatAccountHandler'),
                json.dumps({'license_type': 'rhsm',
                            'username': username,
                            'password': 'password',
                            'release_id': 1}),
                headers=self.default_headers)
            self.assertEquals(resp.status, 200)
            query = self.env.db.query(RedHatAccount)
            self.assertEquals(query.count(), 1)
            self.assertEquals(query.filter_by(username=username).count(), 1)

    @patch('time.sleep')
    @patch('os.kill')
    @patch('os.waitpid')
    def test_timeout_command(self, mock_sleep, mock_kill, mock_waitpid):
        command = 'ls -al'
        settings.RHEL_VALIDATION_TIMEOUT = 0
        with patch('subprocess.Popen') as popen:
            instance = popen.return_value
            instance.poll.return_value = None
            handler = RedHatAccountHandler()
            retval = handler.timeout_command(shlex.split(command))
            self.assertEquals(retval, None)

        with patch('subprocess.Popen') as popen:
            instance = popen.return_value
            instance.stdout.read.return_value = 'stdout'
            instance.stderr.read.return_value = 'stderr'
            handler = RedHatAccountHandler()
            retval = handler.timeout_command(shlex.split(command))
            self.assertEquals(retval, ('stdout', 'stderr'))
