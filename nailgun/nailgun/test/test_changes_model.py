# -*- coding: utf-8 -*-
import json
import time

from mock import patch

from nailgun.settings import settings

import nailgun
import nailgun.rpc as rpc
from nailgun.task.manager import DeploymentTaskManager
from nailgun.task.fake import FAKE_THREADS
from nailgun.task.errors import WrongNodeStatus
from nailgun.test.base import BaseHandlers
from nailgun.test.base import reverse
from nailgun.api.models import Cluster, Task, ClusterChanges


class TestClusterChanges(BaseHandlers):

    def tearDown(self):
        # wait for fake task thread termination
        import threading
        for thread in threading.enumerate():
            if thread is not threading.currentThread():
                if hasattr(thread, "rude_join"):
                    timer = time.time()
                    timeout = 25
                    thread.rude_join(timeout)
                    if time.time() - timer > timeout:
                        raise Exception(
                            '{0} seconds is not enough'
                            ' - possible hanging'.format(
                                timeout
                            )
                        )

    def test_cluster_creation_adds_pending_changes(self):
        cluster = self.create_cluster_api()
        attributes_changes = self.db.query(ClusterChanges).filter_by(
            name="attributes"
        ).all()
        self.assertEquals(len(attributes_changes), 1)
        networks_changes = self.db.query(ClusterChanges).filter_by(
            name="networks"
        ).all()
        self.assertEquals(len(networks_changes), 1)
        all_changes = self.db.query(ClusterChanges).all()
        self.assertEquals(len(all_changes), 2)

    def test_attributes_changing_adds_pending_changes(self):
        cluster = self.create_cluster_api()
        cluster_db = self.db.query(Cluster).get(cluster["id"])
        cluster_db.clear_pending_changes()
        all_changes = self.db.query(ClusterChanges).all()
        self.assertEquals(len(all_changes), 0)
        resp = self.app.put(
            reverse(
                'ClusterAttributesHandler',
                kwargs={'cluster_id': cluster['id']}),
            json.dumps({
                'editable': {
                    "foo": "bar"
                }
            }),
            headers=self.default_headers
        )
        pending_changes = self.db.query(ClusterChanges).filter_by(
            name="attributes"
        ).all()
        self.assertEquals(len(pending_changes), 1)

    def test_default_attributes_adds_pending_changes(self):
        cluster = self.create_cluster_api()
        cluster_db = self.db.query(Cluster).get(cluster["id"])
        cluster_db.clear_pending_changes()
        all_changes = self.db.query(ClusterChanges).all()
        self.assertEquals(len(all_changes), 0)
        resp = self.app.put(
            reverse(
                'ClusterAttributesDefaultsHandler',
                kwargs={'cluster_id': cluster['id']}),
            headers=self.default_headers
        )
        pending_changes = self.db.query(ClusterChanges).filter_by(
            name="attributes"
        ).all()
        self.assertEquals(len(pending_changes), 1)

    def test_network_changing_adds_pending_changes(self):
        cluster = self.create_cluster_api()
        cluster_db = self.db.query(Cluster).get(cluster["id"])
        cluster_db.clear_pending_changes()
        all_changes = self.db.query(ClusterChanges).all()
        self.assertEquals(len(all_changes), 0)
        resp = self.app.put(
            reverse(
                'ClusterSaveNetworksHandler',
                kwargs={'cluster_id': cluster['id']}),
            json.dumps([
                {"id": "1", "access": "restricted"}
            ]),
            headers=self.default_headers
        )
        pending_changes = self.db.query(ClusterChanges).filter_by(
            name="networks"
        ).all()
        self.assertEquals(len(pending_changes), 1)

    @patch('nailgun.task.task.rpc.cast', nailgun.task.task.fake_cast)
    @patch('nailgun.task.task.settings.FAKE_TASKS', True)
    @patch('nailgun.task.fake.settings.FAKE_TASKS_TICK_COUNT', 80)
    @patch('nailgun.task.fake.settings.FAKE_TASKS_TICK_INTERVAL', 1)
    def test_successful_deployment_drops_all_changes(self):
        cluster = self.create_cluster_api()
        node = self.create_default_node(cluster_id=cluster['id'],
                                        role="controller",
                                        status="discover",
                                        pending_addition=True)
        resp = self.app.put(
            reverse(
                'ClusterChangesHandler',
                kwargs={'cluster_id': cluster['id']}),
            headers=self.default_headers
        )
        response = json.loads(resp.body)
        supertask_uuid = response['uuid']
        supertask = self.db.query(Task).filter_by(
            uuid=supertask_uuid
        ).first()

        timer = time.time()
        timeout = 60
        while supertask.status == 'running':
            self.db.refresh(supertask)
            if time.time() - timer > timeout:
                raise Exception("Deployment seems to be hanged")
            time.sleep(1)

        cluster_db = self.db.query(Cluster).get(cluster["id"])
        self.assertEquals(list(cluster_db.changes), [])

    @patch('nailgun.task.task.rpc.cast', nailgun.task.task.fake_cast)
    @patch('nailgun.task.task.settings.FAKE_TASKS', True)
    @patch('nailgun.task.fake.settings.FAKE_TASKS_TICK_COUNT', 80)
    @patch('nailgun.task.fake.settings.FAKE_TASKS_TICK_INTERVAL', 1)
    def test_failed_deployment_does_nothing_with_changes(self):
        cluster = self.create_cluster_api()
        node = self.create_default_node(cluster_id=cluster['id'],
                                        role="controller",
                                        status="error",
                                        error_type="provision")
        resp = self.app.put(
            reverse(
                'ClusterChangesHandler',
                kwargs={'cluster_id': cluster['id']}),
            headers=self.default_headers
        )
        response = json.loads(resp.body)
        supertask_uuid = response['uuid']
        supertask = self.db.query(Task).filter_by(
            uuid=supertask_uuid
        ).first()

        timer = time.time()
        timeout = 60
        while supertask.status == 'running':
            self.db.refresh(supertask)
            if time.time() - timer > timeout:
                raise Exception("Deployment seems to be hanged")
            time.sleep(1)

        attributes_changes = self.db.query(ClusterChanges).filter_by(
            name="attributes"
        ).all()
        self.assertEquals(len(attributes_changes), 1)
        networks_changes = self.db.query(ClusterChanges).filter_by(
            name="networks"
        ).all()
        self.assertEquals(len(networks_changes), 1)
        all_changes = self.db.query(ClusterChanges).all()
        self.assertEquals(len(all_changes), 2)
