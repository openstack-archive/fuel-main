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
        logs_regexp = r'^(?P<date>\w+):(?P<level>\w+):(?P<text>\w+)$'
        settings.update({
            'REMOTE_LOGS_PATH': self.log_dir,
            'REMOTE_LOGS_REGEXP': logs_regexp,
            'REMOTE_LOGS': [{
                'id': 'syslog',
                'name': 'Syslog',
                'path': 'test-syslog.log'
            }]
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
        self.assertEquals(response, settings.REMOTE_LOGS)

    def test_log_entry_collection_handler(self):
        node_ip = '10.20.30.40'
        log_entry = ['date111', 'level222', 'text333']
        cluster = self.create_default_cluster()
        node = self.create_default_node(cluster_id=cluster.id, ip=node_ip)

        node_log_dir = os.path.join(self.log_dir, node_ip)
        os.makedirs(node_log_dir)
        node_log_file = os.path.join(node_log_dir,
                                     settings.REMOTE_LOGS[0]['path'])
        f = open(node_log_file, 'w')
        f.write(':'.join(log_entry))
        f.close()

        resp = self.app.get(
            reverse('LogEntryCollectionHandler'),
            params={'node': node.id, 'source': settings.REMOTE_LOGS[0]['id']},
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
        response = json.loads(resp.body)
        self.assertEquals(response, [log_entry])
