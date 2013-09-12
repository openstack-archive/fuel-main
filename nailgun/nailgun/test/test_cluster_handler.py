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
from mock import patch

import nailgun
from nailgun.api.models import Cluster
from nailgun.api.models import NetworkGroup
from nailgun.api.models import Node
from nailgun.test.base import BaseHandlers
from nailgun.test.base import fake_tasks
from nailgun.test.base import reverse


class TestHandlers(BaseHandlers):

    def delete(self, cluster_id):
        return self.app.delete(
            reverse('ClusterHandler', kwargs={'cluster_id': cluster_id}),
            '',
            headers=self.default_headers
        )

    def test_cluster_get(self):
        cluster = self.env.create_cluster(api=False)
        resp = self.app.get(
            reverse('ClusterHandler', kwargs={'cluster_id': cluster.id}),
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
        response = json.loads(resp.body)
        self.assertEquals(cluster.id, response['id'])
        self.assertEquals(cluster.name, response['name'])
        self.assertEquals(cluster.release.id, response['release']['id'])

    def test_cluster_creation(self):
        release = self.env.create_release(api=False)
        yet_another_cluster_name = 'Yet another cluster'
        resp = self.app.post(
            reverse('ClusterCollectionHandler'),
            params=json.dumps({
                'name': yet_another_cluster_name,
                'release': release.id
            }),
            headers=self.default_headers
        )
        self.assertEquals(201, resp.status)
        response = json.loads(resp.body)
        self.assertEquals(yet_another_cluster_name, response['name'])
        self.assertEquals(release.id, response['release']['id'])

    def test_cluster_update(self):
        updated_name = u'Updated cluster'
        cluster = self.env.create_cluster(api=False)

        clusters_before = len(self.db.query(Cluster).all())

        resp = self.app.put(
            reverse('ClusterHandler', kwargs={'cluster_id': cluster.id}),
            json.dumps({'name': updated_name}),
            headers=self.default_headers
        )
        self.db.refresh(cluster)
        self.assertEquals(resp.status, 200)
        clusters = self.db.query(Cluster).filter(
            Cluster.name == updated_name
        ).all()
        self.assertEquals(len(clusters), 1)
        self.assertEquals(clusters[0].name, updated_name)

        clusters_after = len(self.db.query(Cluster).all())
        self.assertEquals(clusters_before, clusters_after)

    def test_cluster_updates_network_manager(self):
        cluster = self.env.create_cluster(api=False)
        self.assertEquals(cluster.net_manager, "FlatDHCPManager")
        resp = self.app.put(
            reverse('ClusterHandler', kwargs={'cluster_id': cluster.id}),
            json.dumps({'net_manager': 'VlanManager'}),
            headers=self.default_headers
        )
        self.assertEquals(resp.status, 200)
        self.db.refresh(cluster)
        self.assertEquals(cluster.net_manager, "VlanManager")

    def test_cluster_node_list_update(self):
        node1 = self.env.create_node(api=False)
        node2 = self.env.create_node(api=False)
        cluster = self.env.create_cluster(api=False)
        resp = self.app.put(
            reverse('ClusterHandler', kwargs={'cluster_id': cluster.id}),
            json.dumps({'nodes': [node1.id]}),
            headers=self.default_headers
        )
        self.assertEquals(resp.status, 200)

        nodes = self.db.query(Node).filter(Node.cluster == cluster).all()
        self.assertEquals(1, len(nodes))
        self.assertEquals(nodes[0].id, node1.id)

        resp = self.app.put(
            reverse('ClusterHandler', kwargs={'cluster_id': cluster.id}),
            json.dumps({'nodes': [node2.id]}),
            headers=self.default_headers
        )
        self.assertEquals(resp.status, 200)

        nodes = self.db.query(Node).filter(Node.cluster == cluster)
        self.assertEquals(1, nodes.count())

    def test_empty_cluster_deletion(self):
        cluster = self.env.create_cluster(api=True)
        resp = self.delete(cluster['id'])

        self.assertEquals(resp.status, 202)
        self.assertEquals(self.db.query(Node).count(), 0)
        self.assertEquals(self.db.query(Cluster).count(), 0)

    @fake_tasks()
    def test_cluster_deletion(self):
        self.env.create(
            cluster_kwargs={},
            nodes_kwargs=[
                {"pending_addition": True},
                {"status": "ready"}])

        resp = self.delete(self.env.clusters[0].id)
        self.assertEquals(resp.status, 202)

        def cluster_is_empty():
            return self.db.query(Cluster).count() == 0

        self.env.wait_for_true(cluster_is_empty, timeout=5)
        self._wait_for_threads()

        # Nodes should be in discover status
        self.assertEquals(self.db.query(Node).count(), 2)
        for node in self.db.query(Node):
            self.assertEquals(node.status, 'discover')
            self.assertEquals(node.cluster_id, None)

    @fake_tasks()
    def test_cluster_deleteion_with_offline_nodes(self):
        self.env.create(
            cluster_kwargs={},
            nodes_kwargs=[
                {'pending_addition': True},
                {'online': False, 'status': 'ready'}])

        resp = self.delete(self.env.clusters[0].id)
        self.assertEquals(resp.status, 202)

        def cluster_is_empty_and_in_db_one_node():
            return self.db.query(Cluster).count() == 0 and \
                self.db.query(Node).count() == 1

        self.env.wait_for_true(cluster_is_empty_and_in_db_one_node, timeout=5)
        self._wait_for_threads()

        node = self.db.query(Node).first()
        self.assertEquals(node.status, 'discover')
        self.assertEquals(node.cluster_id, None)

    def test_cluster_deletion_delete_networks(self):
        cluster = self.env.create_cluster(api=True)
        cluster_db = self.db.query(Cluster).get(cluster['id'])
        ngroups = [n.id for n in cluster_db.network_groups]
        self.db.delete(cluster_db)
        self.db.commit()
        ngs = self.db.query(NetworkGroup).filter(
            NetworkGroup.id.in_(ngroups)
        ).all()
        self.assertEqual(ngs, [])

    @fake_tasks(fake_rpc=False, mock_rpc=False)
    @patch('nailgun.rpc.cast')
    def test_cluster_orchestrator_data(self, mocked_rpc):
        # creating cluster with nodes
        self.env.create(
            cluster_kwargs={
                'mode': 'ha_compact'
            },
            nodes_kwargs=[
                {'roles': ['controller'], 'pending_addition': True},
                {'roles': ['controller'], 'pending_addition': True},
                {'roles': ['controller', 'cinder'], 'pending_addition': True},
                {'roles': ['compute', 'cinder'], 'pending_addition': True},
                {'roles': ['compute'], 'pending_addition': True},
                {'roles': ['cinder'], 'pending_addition': True}])
        cluster = self.env.clusters[0]
        orchestrator_data = {"field": "test"}
        # assigning facts to cluster
        cluster.facts = orchestrator_data
        self.db.commit()
        self.env.launch_deployment()
        # intercepting arguments with which rpc.cast was called
        args, kwargs = nailgun.task.manager.rpc.cast.call_args
        self.datadiff(orchestrator_data, args[1][0]["args"]["deployment_info"])

    def test_cluster_orchestrator_data_handler(self):
        # creating cluster, cluster.facts default value is {}
        cluster = self.env.create_cluster(api=False)
        # updating facts
        orchestrator_data = {"field": "test"}
        orchestrator_data_json = json.dumps(orchestrator_data)
        put_resp = self.app.put(
            reverse('ClusterOrchestratorData',
                    kwargs={'cluster_id': cluster.id}),
            orchestrator_data_json,
            headers=self.default_headers
        )
        self.assertEquals(put_resp.status, 200)
        self.assertEquals(cluster.facts, orchestrator_data)
        # getting facts
        get_resp = self.app.get(
            reverse('ClusterOrchestratorData',
                    kwargs={'cluster_id': cluster.id}),
            headers=self.default_headers
        )
        self.assertEquals(get_resp.status, 200)
        self.datadiff(orchestrator_data, json.loads(get_resp.body))
        # deleting facts
        delete_resp = self.app.delete(
            reverse('ClusterOrchestratorData',
                    kwargs={'cluster_id': cluster.id}),
            headers=self.default_headers
        )
        self.assertEquals(delete_resp.status, 202)
        self.assertEqual(cluster.facts, {})
