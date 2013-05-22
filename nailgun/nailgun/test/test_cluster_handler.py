# -*- coding: utf-8 -*-
import json
from nailgun.api.models import Cluster, Node, NetworkGroup
from nailgun.test.base import BaseHandlers
from nailgun.test.base import reverse
from nailgun.test.base import fake_tasks

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
