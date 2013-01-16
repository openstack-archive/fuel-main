# -*- coding: utf-8 -*-

import unittest
import tempfile
import shutil
import time
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
        regexp = (r'^(?P<date>\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}):'
                  '(?P<level>\w+):(?P<text>\w+)$')
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
        node = self.create_default_node(ip=node_ip)

        resp = self.app.get(
            reverse('LogSourceByNodeCollectionHandler',
                    kwargs={'node_id': node.id}),
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
        response = json.loads(resp.body)
        self.assertEquals(response, [])

        log_entry = ['date111', 'level222', 'text333']
        self._create_logfile_for_node(settings.LOGS[1], log_entry, node)
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
        log_entry = [time.strftime(settings.UI_LOG_DATE_FORMAT),
                     'LEVEL222', 'text333']
        cluster = self.create_default_cluster()
        node = self.create_default_node(cluster_id=cluster.id, ip=node_ip)
        self._create_logfile_for_node(settings.LOGS[0], log_entry)
        self._create_logfile_for_node(settings.LOGS[1], log_entry, node)

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

    def _create_logfile_for_node(self, log_config, log_entry, node=None):
        if log_config['remote']:
            log_dir = os.path.join(self.log_dir, node.ip)
            not os.path.isdir(log_dir) and os.makedirs(log_dir)
            log_file = os.path.join(log_dir, log_config['path'])
        else:
            log_file = log_config['path']
        with open(log_file, 'w') as f:
            f.write(':'.join(log_entry))
