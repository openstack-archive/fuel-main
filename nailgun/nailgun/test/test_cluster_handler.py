# -*- coding: utf-8 -*-
import json
from paste.fixture import TestApp

from nailgun.api.models import Cluster, Node
from nailgun.test.base import BaseHandlers
from nailgun.test.base import reverse


class TestHandlers(BaseHandlers):
    def test_cluster_delete(self):
        cluster = self.create_default_cluster()
        resp = self.app.delete(
            reverse('ClusterHandler', kwargs={'cluster_id': cluster.id}),
            headers=self.default_headers
        )
        self.assertEquals(202, resp.status)
        self.assertEquals('', resp.body)

    def test_cluster_get(self):
        cluster = self.create_default_cluster()
        resp = self.app.get(
            reverse('ClusterHandler', kwargs={'cluster_id': cluster.id}),
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
        response = json.loads(resp.body)
        self.assertEquals(cluster.id, response['id'])
        self.assertEquals(cluster.name, response['name'])
        self.assertEquals(cluster.nodes, response['nodes'])
        self.assertEquals(cluster.release.id, response['release']['id'])

    def test_cluster_creation_without_nodes(self):
        release = self.create_default_release()
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
        self.assertEquals([], response['nodes'])
        self.assertEquals(release.id, response['release']['id'])

    def test_cluster_creation_with_nodes(self):
        release = self.create_default_release()
        node = self.create_default_node()
        yet_another_cluster_name = u'Yet another cluster'
        resp = self.app.post(
            reverse('ClusterCollectionHandler'),
            params=json.dumps({
                'name': yet_another_cluster_name,
                'release': release.id,
                'nodes': [node.id]
            }),
            headers=self.default_headers
        )
        self.assertEquals(201, resp.status)
        response = json.loads(resp.body)
        self.assertEquals(yet_another_cluster_name, response['name'])
        self.assertEquals(1, len(response['nodes']))
        self.assertEquals(release.id, response['release']['id'])

    def test_cluster_update(self):
        updated_name = u'Updated cluster'
        cluster = self.create_default_cluster()

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
        cluster = self.create_default_cluster()
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
        node1 = self.create_default_node()
        node2 = self.create_default_node()
        cluster = self.create_default_cluster()
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
            reverse('ClusterHandler', kwargs={'cluster_id': 1}),
            json.dumps({'nodes': [node2.id]}),
            headers=self.default_headers
        )
        self.assertEquals(resp.status, 200)

        nodes = self.db.query(Node).filter(Node.cluster == cluster)
        self.assertEquals(1, nodes.count())
