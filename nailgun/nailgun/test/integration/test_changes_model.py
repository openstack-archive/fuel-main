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

import json

from nailgun.api.models import Cluster
from nailgun.api.models import ClusterChanges
from nailgun.test.base import BaseIntegrationTest
from nailgun.test.base import fake_tasks
from nailgun.test.base import reverse


class TestClusterChanges(BaseIntegrationTest):

    def tearDown(self):
        self._wait_for_threads()
        super(TestClusterChanges, self).tearDown()

    def test_cluster_creation_adds_pending_changes(self):
        self.env.create_cluster(api=True)
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

    def test_node_volumes_modification_adds_pending_changes(self):
        cluster = self.env.create_cluster(api=True)
        self.env.create_node(
            api=True,
            cluster_id=cluster["id"]
        )
        node_db = self.env.nodes[0]
        node_disks_changes = self.db.query(ClusterChanges).filter_by(
            name="disks",
            node_id=node_db.id
        ).all()
        self.assertEquals(len(node_disks_changes), 1)
        resp = self.app.get(
            reverse(
                'ClusterHandler',
                kwargs={'cluster_id': cluster['id']}),
            headers=self.default_headers
        )
        response = json.loads(resp.body)
        self.assertIn(
            ["disks", node_db.id],
            response["changes"]
        )

    def test_node_volumes_clears_after_deletion_from_cluster(self):
        cluster = self.env.create_cluster(api=True)
        self.env.create_node(
            api=True,
            cluster_id=cluster["id"]
        )
        node_db = self.env.nodes[0]
        node_disks_changes = self.db.query(ClusterChanges).filter_by(
            name="disks",
            node_id=node_db.id
        ).all()
        self.assertEquals(len(node_disks_changes), 1)
        self.app.put(
            reverse('NodeCollectionHandler'),
            json.dumps([{"id": node_db.id, "cluster_id": None}]),
            headers=self.default_headers
        )
        self.env.refresh_clusters()
        node_disks_changes = self.db.query(ClusterChanges).filter_by(
            name="disks",
            node_id=node_db.id
        ).all()
        self.assertEquals(len(node_disks_changes), 0)

    def test_attributes_changing_adds_pending_changes(self):
        cluster = self.env.create_cluster(api=True)
        cluster_db = self.env.clusters[0]
        cluster_db.clear_pending_changes()
        all_changes = self.db.query(ClusterChanges).all()
        self.assertEquals(len(all_changes), 0)
        self.app.put(
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
        self.app.put(
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
        resp = self.app.get(
            reverse(
                'NetworkConfigurationHandler',
                kwargs={'cluster_id': cluster['id']}),
            headers=self.default_headers
        )
        net_id = json.loads(resp.body)['networks'][0]["id"]
        resp = self.app.put(
            reverse(
                'NetworkConfigurationHandler',
                kwargs={'cluster_id': cluster['id']}),
            json.dumps({'networks': [{
                "id": net_id, "access": "restricted"}
            ]}),
            headers=self.default_headers
        )
        pending_changes = self.db.query(ClusterChanges).filter_by(
            name="networks"
        ).all()
        self.assertEquals(len(pending_changes), 1)

    @fake_tasks()
    def test_successful_deployment_drops_all_changes(self):
        self.env.create(
            nodes_kwargs=[
                {"api": True, "pending_addition": True}
            ]
        )
        supertask = self.env.launch_deployment()
        self.env.wait_ready(supertask, 60)
        cluster_db = self.db.query(Cluster).get(
            self.env.clusters[0].id
        )
        self.assertEquals(list(cluster_db.changes), [])

    @fake_tasks()
    def test_failed_deployment_does_nothing_with_changes(self):
        cluster = self.env.create_cluster(api=True)
        self.env.create_node(
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
