# -*- coding: utf-8 -*-
import unittest
import json
from unittest import TestCase
from paste.fixture import TestApp
from db import syncdb, flush, dropdb
from sqlalchemy import orm
from api.models import Cluster, Node, Release, engine
from base import reverse
from manage import app


class TestHandlers(TestCase):
    @classmethod
    def setUpClass(cls):
        dropdb()
        syncdb()

    def setUp(self):
        self.app = TestApp(app.wsgifunc())
        self.db = orm.scoped_session(orm.sessionmaker(bind=engine))()
        self.default_headers = {
            "Content-Type": "application/json"
        }
        flush()

    def default_metadata(self):
        metadata = {'block_device': 'new-val',
                    'interfaces': 'd',
                    'cpu': 'u',
                    'memory': 'a'}
        return metadata

    def create_release(self):
        resp = self.app.post(
            '/api/releases',
            params=json.dumps({
                'name': 'Another test release',
                'version': '1.0'
            }),
            headers=self.default_headers
        )
        self.assertEquals(resp.status, 201)

    def create_default_node(self):
        node = Node()
        node.mac = u"ASDFGHJKLMNOPR"
        self.db.add(node)
        self.db.commit()
        return node

#    def create_default_role(self):
#        role = Role()
#        role.name = u"role Name"
#        role.release = self.create_default_release()
#        self.db.add(role)
#        self.db.commit()
#        return role

    def create_default_release(self):
        release = Release()
        release.name = u"release_name"
        release.version = 5
        self.db.add(release)
        self.db.commit()
        return release

    def create_default_cluster(self):
        cluster = Cluster()
        cluster.name = u"bu"
        cluster.release = self.create_default_release()
        self.db.add(cluster)
        self.db.commit()
        return cluster

    def test_release_creation(self):
        resp = self.app.post(
            '/api/releases',
            params=json.dumps({
                'name': 'Another test release',
                'version': '1.0'
            }),
            headers=self.default_headers
        )
        self.assertEquals(resp.status, 201)

    def test_cluster_creation_pass(self):
        pass
#        release = self.create_default_release()
#        yet_another_cluster_name = 'Yet another cluster'
#        resp = self.app.post(
#             '/api/clusters',
#             params=json.dumps({
#                 'name': yet_another_cluster_name,
#                 'release': release.id
#             }),
#             headers = self.default_headers
#        )
#        self.assertEquals(resp.status, 201)
#
#        clusters_from_db = self.db.query(Cluster).filter(
#             Cluster.name==yet_another_cluster_name
#        )
#        self.assertEquals(len(clusters_from_db), 1)
#        cluster = clusters_from_db[0]
#        self.assertEquals(cluster.nodes.all()[0].id,
#           self.create_default_node().id)
#        self.assertEquals(len(cluster.release.networks.all()), 3)
#        # test delete
#        resp = self.app.delete(
#             reverse('ClusterHandler', kwargs={'cluster_id': cluster.id}),
#             "",
#             headers = self.default_headers
#        )
#        self.assertEquals(resp.status, 204)

    def test_all_api_urls_404(self):
        test_urls = {}
        url_ids = {
            'ClusterHandler': {'cluster_id': 1},
            'NodeHandler': {'node_id': 1},
            'ReleaseHandler': {'release_id': 1},
        }

        skip_urls = [
        ]

        for url, methods in test_urls.iteritems():
            if url in skip_urls:
                continue
            kwargs = {}
            if url in url_ids:
                kwargs = url_ids[url]

            test_url = reverse(url, kwargs=kwargs)
            resp = self.app.get(test_url)
            self.assertEqual(resp.status, 404)

    def test_cluster_creation(self):
        self.create_release()
        self.create_default_node()
        yet_another_cluster_name = u'Yet another cluster'
        resp = self.app.post(
            '/api/clusters',
            params=json.dumps({
                'name': yet_another_cluster_name,
                'release': 1,
                'nodes': []
            }),
            headers=self.default_headers
        )
        self.assertEquals(resp.status, 201)

        cluster = self.db.query(Cluster).filter(
            Cluster.name == yet_another_cluster_name
        ).first()

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
        self.assertEquals(2, nodes.count())

    def test_node_creation_with_id(self):
        node_id = '080000000003'
        resp = self.app.post(
            reverse('NodeCollectionHandler'),
            json.dumps({'id': node_id}),
            headers=self.default_headers,
            expect_errors=True)
        self.assertEquals(resp.status, 400)

    def test_node_creation(self):
        resp = self.app.post(
            reverse('NodeCollectionHandler'),
            json.dumps({'mac': 'ASDFAAASDFAA'}),
            headers=self.default_headers)
        self.assertEquals(resp.status, 201)

        nodes = self.db.query(Node).filter(Node.mac == 'ASDFAAASDFAA')
        self.assertEquals(1, nodes.count())

    def test_node_deletion(self):
        node = self.create_default_node()
        resp = self.app.delete(
            reverse('NodeHandler', kwargs={'node_id': node.id}),
            "",
            headers=self.default_headers,
            expect_errors=True
        )
        self.assertEquals(resp.status, 204)

    @unittest.skip('wth?')
    def test_node_creation_using_put(self):
        node_id = '080000000002'

        resp = self.app.put(
            reverse('NodeHandler', kwargs={'node_id': node_id}),
            json.dumps({}),
            headers=self.default_headers)
        self.assertEquals(resp.status, 200)

        nodes_from_db = self.db.query(Node).filter(id=node_id)
        self.assertEquals(len(nodes_from_db), 1)

    def test_node_valid_metadata_gets_updated(self):
        new_metadata = self.default_metadata()
        node = self.create_default_node()
        resp = self.app.put(
            reverse('NodeHandler', kwargs={'node_id': node.id}),
            json.dumps({'meta': new_metadata}),
            headers=self.default_headers)
        self.assertEquals(resp.status, 200)
        self.db.refresh(node)

        nodes = self.db.query(Node).filter(
            Node.id == node.id
        ).all()
        self.assertEquals(len(nodes), 1)
        self.assertEquals(nodes[0].meta, new_metadata)

    def test_node_valid_status_gets_updated(self):
        node = self.create_default_node()
        params = {'status': 'error'}
        resp = self.app.put(
            reverse('NodeHandler', kwargs={'node_id': node.id}),
            json.dumps(params),
            headers=self.default_headers)
        self.assertEquals(resp.status, 200)

    def test_node_valid_list_of_new_roles_gets_updated(self):
        node = self.create_default_node()
        resp = self.app.put(
            reverse('NodeHandler', kwargs={'node_id': node.id}),
            json.dumps({
                'redeployment_needed': True
            }),
            headers=self.default_headers
        )
        self.assertEquals(resp.status, 200)
        self.db.refresh(node)

        node_from_db = self.db.query(Node).filter(
            Node.id == node.id
        ).first()
        self.assertEquals(node_from_db.redeployment_needed, True)

    def test_put_returns_400_if_no_body(self):
        node = self.create_default_node()
        resp = self.app.put(
            reverse('NodeHandler', kwargs={'node_id': node.id}),
            "",
            headers=self.default_headers,
            expect_errors=True)
        self.assertEquals(resp.status, 400)

    def test_put_returns_415_if_wrong_content_type(self):
        node = self.create_default_node()
        resp = self.app.put(
            reverse('NodeHandler', kwargs={'node_id': node.id}),
            json.dumps({'meta': json.dumps(self.default_metadata())}),
            headers={"Content-Type": "plain/text"},
            expect_errors=True
        )
        self.assertEquals(resp.status, 415)

    def test_put_returns_400_if_wrong_status(self):
        node = self.create_default_node()
        params = {'status': 'invalid_status'}
        resp = self.app.put(
            reverse('NodeHandler', kwargs={'node_id': node.id}),
            json.dumps(params),
            headers=self.default_headers,
            expect_errors=True)
        print resp
        self.assertEquals(resp.status, 400)

    @unittest.skip('no validation of metadata')
    def test_put_returns_400_if_no_block_device_attr(self):
        node = self.create_default_node()
        old_meta = self.create_default_node().metadata
        new_meta = self.default_metadata()
        del new_meta['block_device']
        resp = self.app.put(
            reverse('NodeHandler', kwargs={'node_id': node.id}),
            json.dumps({'metadata': new_meta}),
            headers=self.default_headers,
            expect_errors=True)
        self.assertEquals(resp.status, 400)

        node_from_db = Node.objects.get(id=self.create_default_node().id)
        self.assertEquals(node_from_db.metadata, old_meta)

    @unittest.skip('no validation of metadata')
    def test_put_returns_400_if_no_interfaces_attr(self):
        node = self.create_default_node()
        old_meta = self.create_default_node().metadata
        new_meta = self.default_metadata()
        del new_meta['interfaces']
        resp = self.app.put(
            reverse('NodeHandler', kwargs={'node_id': node.id}),
            json.dumps({'metadata': new_meta}),
            headers=self.default_headers,
            expect_errors=True)
        self.assertEquals(resp.status, 400)

        node_from_db = Node.objects.get(id=self.create_default_node().id)
        self.assertEquals(node_from_db.metadata, old_meta)

    @unittest.skip('no validation of metadata')
    def test_put_returns_400_if_interfaces_empty(self):
        node = self.create_default_node()
        old_meta = node.metadata
        new_meta = {'asdf': ['fdsa', 'asdf'], 'interfaces': ""}
        resp = self.app.put(
            reverse('NodeHandler', kwargs={'node_id': node.id}),
            json.dumps({'metadata': new_meta}),
            headers=self.default_headers,
            expect_errors=True)
        self.assertEquals(resp.status, 400)

        node_from_db = Node.objects.get(id=node.id)
        self.assertEquals(node_from_db.metadata, old_meta)

    @unittest.skip('no validation of metadata')
    def test_put_returns_400_if_no_cpu_attr(self):
        node = self.create_default_node()
        old_meta = self.create_default_node().metadata
        new_meta = self.default_metadata()
        del new_meta['cpu']
        resp = self.app.put(
            reverse('NodeHandler', kwargs={'node_id': node.id}),
            json.dumps({'metadata': new_meta}),
            headers=self.default_headers,
            expect_errors=True)
        self.assertEquals(resp.status, 400)

        node_from_db = Node.objects.get(id=self.create_default_node().id)
        self.assertEquals(node_from_db.metadata, old_meta)

    @unittest.skip('no validation of metadata')
    def test_put_returns_400_if_no_memory_attr(self):
        node = self.create_default_node()
        old_meta = self.create_default_node().metadata
        new_meta = self.default_metadata()
        del new_meta['memory']
        resp = self.app.put(
            reverse('NodeHandler', kwargs={'node_id': node.id}),
            json.dumps({'metadata': new_meta}),
            headers=self.default_headers,
            expect_errors=True)
        self.assertEquals(resp.status, 400)

        node_from_db = Node.objects.get(id=self.create_default_node().id)
        self.assertEquals(node_from_db.metadata, old_meta)

    def test_release_create(self):
        release_name = "OpenStack"
        release_version = "1.0.0"
        release_description = "This is test release"
        resp = self.app.post(
            reverse('ReleaseCollectionHandler'),
            json.dumps({
                'name': release_name,
                'version': release_version,
                'description': release_description,
                'networks_metadata': [
                    {"name": "floating", "access": "public"},
                    {"name": "fixed", "access": "private"},
                    {"name": "storage", "access": "private"}
                ]
            }),
            headers=self.default_headers
        )
        self.assertEquals(resp.status, 201)

        resp = self.app.post(
            reverse('ReleaseCollectionHandler'),
            json.dumps({
                'name': release_name,
                'version': release_version,
                'description': release_description,
                'networks_metadata': [
                    {"name": "fixed", "access": "private"}
                ]
            }),
            headers=self.default_headers,
            expect_errors=True
        )
        self.assertEquals(resp.status, 409)

        release_from_db = self.db.query(Release).filter(
            Release.name == release_name,
            Release.version == release_version,
            Release.description == release_description
        ).all()
        self.assertEquals(len(release_from_db), 1)

    @unittest.skip("obsolete")
    def test_network_create(self):
        network_data = {
            "name": "test_network",
            "network": "10.0.0.0/24",
            "range_l": "10.0.0.5",
            "range_h": "10.0.0.10",
            "gateway": "10.0.0.1",
            "vlan_id": 100,
            "release": 1,
            "access": "public"
        }
        resp = self.app.post(
            reverse('NetworkCollectionHandler'),
            json.dumps(network_data),
            headers=self.default_headers
        )
        self.assertEquals(resp.status, 201)
        resp = self.app.post(
            reverse('NetworkCollectionHandler'),
            json.dumps(network_data),
            headers=self.default_headers,
            expect_errors=True
        )
        self.assertEquals(resp.status, 409)
        network_data["network"] = "test_fail"
        resp = self.app.post(
            reverse('NetworkCollectionHandler'),
            json.dumps(network_data),
            headers=self.default_headers,
            expect_errors=True
        )
        self.assertEqual(resp.status, 400)
