# -*- coding: utf-8 -*-

import unittest
import tempfile
import shutil
import json
import os

from nailgun.test.base import BaseHandlers
from nailgun.test.base import reverse

from nailgun.settings import settings


class TestLogs(BaseHandlers):

    def setUp(self):
        super(TestLogs, self).setUp()
        self.log_dir = tempfile.mkdtemp()
        self.local_log_file = os.path.join(self.log_dir, 'nailgun.log')
        settings.update({
            'LOGS': [
                {
                    'id': 'nailgun',
                    'name': 'Nailgun',
                    'remote': False,
                    'regexp': r'^(?P<date>\w+):(?P<level>\w+):(?P<text>\w+)$',
                    'levels': [],
                    'path': self.local_log_file
                }, {
                    'id': 'syslog',
                    'name': 'Syslog',
                    'remote': True,
                    'regexp': r'^(?P<date>\w+):(?P<level>\w+):(?P<text>\w+)$',
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

    def test_log_entry_collection_handler(self):
        node_ip = '10.20.30.40'
        log_entry = ['date111', 'LEVEL222', 'text333']
        cluster = self.create_default_cluster()
        node = self.create_default_node(cluster_id=cluster.id, ip=node_ip)

        remote_log_dir = os.path.join(self.log_dir, node_ip)
        os.makedirs(remote_log_dir)
        remote_log_file = os.path.join(remote_log_dir,
                                       settings.LOGS[1]['path'])
        for log_file in (remote_log_file, self.local_log_file):
            with open(log_file, 'w') as f:
                f.write(':'.join(log_entry))

        resp = self.app.get(
            reverse('LogEntryCollectionHandler'),
            params={'source': settings.LOGS[0]['id']},
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
        response = json.loads(resp.body)
        self.assertEquals(response['entries'], [log_entry])

        resp = self.app.get(
            reverse('LogEntryCollectionHandler'),
            params={'node': node.id, 'source': settings.LOGS[1]['id']},
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
        response = json.loads(resp.body)
        self.assertEquals(response['entries'], [log_entry])
