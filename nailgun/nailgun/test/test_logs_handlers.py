# -*- coding: utf-8 -*-

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

import gzip
import json
import os
import shutil
from StringIO import StringIO
import tarfile
import tempfile
import time

from nailgun.test.base import BaseHandlers
from nailgun.test.base import reverse

from nailgun.settings import settings

from nailgun.api.handlers.logs import read_backwards
from nailgun.api.models import RedHatAccount


class TestLogs(BaseHandlers):

    def setUp(self):
        super(TestLogs, self).setUp()
        self.log_dir = tempfile.mkdtemp()
        self.local_log_file = os.path.join(self.log_dir, 'nailgun.log')
        regexp = (r'^(?P<date>\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}):'
                  '(?P<level>\w+):(?P<text>.+)$')
        settings.update({
            'LOGS': [
                {
                    'id': 'nailgun',
                    'name': 'Nailgun',
                    'remote': False,
                    'regexp': regexp,
                    'date_format': settings.UI_LOG_DATE_FORMAT,
                    'levels': [],
                    'path': self.local_log_file
                }, {
                    'id': 'syslog',
                    'name': 'Syslog',
                    'remote': True,
                    'regexp': regexp,
                    'date_format': settings.UI_LOG_DATE_FORMAT,
                    'base': self.log_dir,
                    'levels': [],
                    'path': 'test-syslog.log'
                }
            ]
        })

    def tearDown(self):
        shutil.rmtree(self.log_dir)
        super(TestLogs, self).tearDown()

    def test_log_source_collection_handler(self):
        resp = self.app.get(
            reverse('LogSourceCollectionHandler'),
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
        response = json.loads(resp.body)
        self.assertEquals(response, settings.LOGS)

    def test_log_source_by_node_collection_handler(self):
        node_ip = '40.30.20.10'
        node = self.env.create_node(api=False, ip=node_ip)

        resp = self.app.get(
            reverse('LogSourceByNodeCollectionHandler',
                    kwargs={'node_id': node.id}),
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
        response = json.loads(resp.body)
        self.assertEquals(response, [])

        log_entry = ['date111', 'level222', 'text333']
        self._create_logfile_for_node(settings.LOGS[1], [log_entry], node)
        resp = self.app.get(
            reverse('LogSourceByNodeCollectionHandler',
                    kwargs={'node_id': node.id}),
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
        response = json.loads(resp.body)
        self.assertEquals(response, [settings.LOGS[1]])

    def test_log_entry_collection_handler(self):
        node_ip = '10.20.30.40'
        log_entries = [
            [
                time.strftime(settings.UI_LOG_DATE_FORMAT),
                'LEVEL111',
                'text1',
            ],
            [
                time.strftime(settings.UI_LOG_DATE_FORMAT),
                'LEVEL222',
                'text2',
            ],
        ]
        cluster = self.env.create_cluster(api=False)
        node = self.env.create_node(cluster_id=cluster.id, ip=node_ip)
        self._create_logfile_for_node(settings.LOGS[0], log_entries)
        self._create_logfile_for_node(settings.LOGS[1], log_entries, node)

        resp = self.app.get(
            reverse('LogEntryCollectionHandler'),
            params={'source': settings.LOGS[0]['id']},
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
        response = json.loads(resp.body)
        response['entries'].reverse()
        self.assertEquals(response['entries'], log_entries)

        resp = self.app.get(
            reverse('LogEntryCollectionHandler'),
            params={'node': node.id, 'source': settings.LOGS[1]['id']},
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
        response = json.loads(resp.body)
        response['entries'].reverse()
        self.assertEquals(response['entries'], log_entries)

    def test_multiline_log_entry(self):
        settings.LOGS[0]['multiline'] = True
        log_entries = [
            [
                time.strftime(settings.UI_LOG_DATE_FORMAT),
                'LEVEL111',
                'text1',
            ],
            [
                time.strftime(settings.UI_LOG_DATE_FORMAT),
                'LEVEL222',
                'text\nmulti\nline',
            ],
            [
                time.strftime(settings.UI_LOG_DATE_FORMAT),
                'LEVEL333',
                'text3',
            ],
        ]
        self.env.create_cluster(api=False)
        self._create_logfile_for_node(settings.LOGS[0], log_entries)

        resp = self.app.get(
            reverse('LogEntryCollectionHandler'),
            params={'source': settings.LOGS[0]['id']},
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
        response = json.loads(resp.body)
        response['entries'].reverse()
        self.assertEquals(response['entries'], log_entries)
        settings.LOGS[0]['multiline'] = False

    def test_backward_reader(self):
        f = tempfile.TemporaryFile(mode='r+')
        forward_lines = []
        backward_lines = []

        # test empty files
        forward_lines = list(f)
        backward_lines = list(read_backwards(f))
        backward_lines.reverse()
        self.assertEquals(forward_lines, backward_lines)

        # filling file with content
        contents = [
            'Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do',
            'eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut',
            'enim ad minim veniam, quis nostrud exercitation ullamco laboris',
            'nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor',
            'in reprehenderit in voluptate velit esse cillum dolore eu fugiat',
            'nulla pariatur. Excepteur sint occaecat cupidatat non proident,',
            'sunt in culpa qui officia deserunt mollit anim id est laborum.',
        ]
        for i in range(5):
            for line in contents:
                f.write('%s\n' % line)

        # test with different buffer sizes
        for bufsize in (1, 5000):
            f.seek(0)

            # test full file reading
            forward_lines = list(f)
            backward_lines = list(read_backwards(f, bufsize))
            backward_lines.reverse()
            self.assertEquals(forward_lines, backward_lines)

            # test partial file reading from middle to beginning
            forward_lines = []
            for i in range(2 * len(contents)):
                forward_lines.append(f.readline())
            backward_lines = list(read_backwards(f, bufsize))
            backward_lines.reverse()
            self.assertEquals(forward_lines, backward_lines)

        f.close()

    def _create_logfile_for_node(self, log_config, log_entries, node=None):
        if log_config['remote']:
            log_dir = os.path.join(self.log_dir, node.ip)
            not os.path.isdir(log_dir) and os.makedirs(log_dir)
            log_file = os.path.join(log_dir, log_config['path'])
        else:
            log_file = log_config['path']
        with open(log_file, 'w') as f:
            for log_entry in log_entries:
                f.write(':'.join(log_entry) + '\n')
                f.flush()

    def test_log_package_handler(self):
        f = tempfile.NamedTemporaryFile(mode='r+b')
        f.write('testcontent')
        f.flush()
        settings.LOGS_TO_PACK_FOR_SUPPORT = {'test': f.name}
        resp = self.app.get(reverse('LogPackageHandler'))
        self.assertEquals(200, resp.status)
        tf = tarfile.open(fileobj=StringIO(resp.body), mode='r:gz')
        m = tf.extractfile('test')
        self.assertEquals(m.read(), 'testcontent')
        f.close()
        m.close()

    def test_log_package_handler_sensitive(self):
        account = RedHatAccount()
        account.username = "REDHATUSERNAME"
        account.password = "REDHATPASSWORD"
        account.license_type = "rhsm"
        self.db.add(account)
        self.db.commit()

        f = tempfile.NamedTemporaryFile(mode='r+b')
        f.write('begin\nREDHATUSERNAME\nREDHATPASSWORD\nend')
        f.flush()
        settings.LOGS_TO_PACK_FOR_SUPPORT = {'test': f.name}
        resp = self.app.get(reverse('LogPackageHandler'))
        self.assertEquals(200, resp.status)
        tf = tarfile.open(fileobj=StringIO(resp.body), mode='r:gz')
        m = tf.extractfile('test')
        self.assertEquals(m.read(), 'begin\nusername\npassword\nend')
        f.close()
        m.close()

    def test_log_package_handler_sensitive_gz(self):
        account = RedHatAccount()
        account.username = "REDHATUSERNAME"
        account.password = "REDHATPASSWORD"
        account.license_type = "rhsm"
        self.db.add(account)
        self.db.commit()

        f = tempfile.NamedTemporaryFile(mode='r+b', suffix='.gz')
        fgz = gzip.GzipFile(mode='w+b', fileobj=f)
        fgz.write('begin\nREDHATUSERNAME\nREDHATPASSWORD\nend')
        fgz.flush()
        fgz.close()

        settings.LOGS_TO_PACK_FOR_SUPPORT = {'test.gz': f.name}
        resp = self.app.get(reverse('LogPackageHandler'))
        self.assertEquals(200, resp.status)
        tf = tarfile.open(fileobj=StringIO(resp.body), mode='r:gz')

        m = tf.extractfile('test.gz')
        mgz = gzip.GzipFile(mode='r+b', fileobj=m)
        self.assertEquals(mgz.read(), 'begin\nusername\npassword\nend')
        mgz.close()

        f.close()
        m.close()

    def test_log_entry_collection_handler_sensitive(self):
        account = RedHatAccount()
        account.username = "REDHATUSERNAME"
        account.password = "REDHATPASSWORD"
        account.license_type = "rhsm"
        self.db.add(account)
        self.db.commit()

        log_entries = [
            [
                time.strftime(settings.UI_LOG_DATE_FORMAT),
                'LEVEL111',
                'begin REDHATUSERNAME REDHATPASSWORD end',
            ],
        ]
        response_log_entries = [
            [
                time.strftime(settings.UI_LOG_DATE_FORMAT),
                'LEVEL111',
                'begin username password end',
            ],
        ]
        self._create_logfile_for_node(settings.LOGS[0], log_entries)
        resp = self.app.get(
            reverse('LogEntryCollectionHandler'),
            params={'source': settings.LOGS[0]['id']},
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
        response = json.loads(resp.body)
        response['entries'].reverse()
        self.assertEquals(response['entries'], response_log_entries)
