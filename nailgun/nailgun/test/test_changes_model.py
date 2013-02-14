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
from nailgun.test.base import fake_tasks
from nailgun.api.models import Cluster, Task, ClusterChanges


class TestClusterChanges(BaseHandlers):

    def tearDown(self):
        self._wait_for_threads()

    def test_cluster_creation_adds_pending_changes(self):
        cluster = self.env.create_cluster(api=True)
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
        cluster = self.env.create_cluster(api=True)
        cluster_db = self.env.clusters[0]
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
        cluster = self.env.create_cluster(api=True)
        cluster_db = self.env.clusters[0]
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
        cluster = self.env.create_cluster(api=True)
        cluster_db = self.env.clusters[0]
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

    @fake_tasks
    def test_successful_deployment_drops_all_changes(self):
        cluster = self.env.create_cluster(api=True)
        node = self.env.create_node(cluster_id=cluster["id"])

        supertask = self.env.launch_deployment()
        self.env.wait_ready(supertask, 60)

        cluster_db = self.db.query(Cluster).get(cluster["id"])
        self.assertEquals(list(cluster_db.changes), [])

    @fake_tasks
    def test_failed_deployment_does_nothing_with_changes(self):
        cluster = self.env.create_cluster(api=True)
        node = self.env.create_node(
            cluster_id=cluster["id"],
            status="error",
            error_type="provision"
        )

        supertask = self.env.launch_deployment()
        self.env.wait_error(supertask, 60)
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
