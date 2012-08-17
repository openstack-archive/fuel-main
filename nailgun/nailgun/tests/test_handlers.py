import simplejson as json
import mock
import celery
from django import http
from django.test import TestCase
from django.db.models import Model
from django.core.urlresolvers import reverse, NoReverseMatch

from piston.emitters import Emitter

from nailgun import models
from nailgun.models import Cluster
from nailgun.models import Node
from nailgun.models import Role
from nailgun.models import Release
from nailgun.models import Com
from nailgun.models import Point
from nailgun.models import EndPoint
from nailgun.api import urls as api_urls
from nailgun import tasks


# monkey patch!
def _construct_monkey(func):
    def wrapped(self=None, *args, **kwargs):
        if isinstance(self.data, Model):
            raise NotImplementedError("Don't return model from handler!")
        return func(self, *args, **kwargs)
    return wrapped

Emitter.construct = _construct_monkey(Emitter.construct)


class TestHandlers(TestCase):

    fixtures = ['default_cluster']

    def setUp(self):
        self.request = http.HttpRequest()

        self.new_meta = {'block_device': 'new-val',
                         'interfaces': 'd',
                         'cpu': 'u',
                         'memory': 'a'
                        }

        self.clusters = models.Cluster.objects.all()
        self.releases = models.Release.objects.all()
        self.roles = models.Role.objects.all()
        self.nodes = models.Node.objects.all()
        self.points = models.Point.objects.all()
        self.com = models.Com.objects.all()
        self.node_url = reverse('node_handler',
                                kwargs={'node_id': self.nodes[0].id})

        self.meta_json = json.dumps(self.new_meta)

    def tearDown(self):
        pass

    def test_all_api_urls_500(self):
        test_urls = {}
        for pattern in api_urls.urlpatterns:
            test_urls[pattern.name] = pattern.callback.handler.allowed_methods

        url_ids = {
            'cluster_handler': {'cluster_id': self.clusters[0].id},
            'node_handler': {'node_id': 'A' * 12},
            'task_handler': {'task_id': 'a' * 36},
            'network_handler': {'network_id': 1},
            'release_handler': {'release_id': self.releases[0].id},
            'role_handler': {'role_id': self.roles[0].id},
            'endpoint_handler': {'node_id': self.nodes[0].id,
                    'component_name': 'abc'},
            'point_handler': {'point_id': self.points[0].id},
            'com_handler': {'component_id': self.com[0].id},
            'node_role_available': {
                'node_id': 'A' * 12,
                'role_id': self.roles[0].id
                },
            'deployment_type_collection_handler': {
                'cluster_id': self.clusters[0].id
                },
        }

        skip_urls = [
            'task_handler'
        ]

        for url, methods in test_urls.iteritems():
            if url in skip_urls:
                continue
            kw = {}
            if url in url_ids:
                kw = url_ids[url]

            if 'GET' in methods:
                test_url = reverse(url, kwargs=kw)
                resp = self.client.get(test_url)
                self.assertNotEqual(str(resp.status_code)[0], '5')

    def test_cluster_creation(self):
        yet_another_cluster_name = 'Yet another cluster'
        resp = self.client.post(
            reverse('cluster_collection_handler'),
            json.dumps({
                'name': yet_another_cluster_name,
                'release': 1,
                'nodes': [self.nodes[0].id],
            }),
            "application/json"
        )
        self.assertEquals(resp.status_code, 200)

        clusters_from_db = Cluster.objects.filter(
            name=yet_another_cluster_name
        )
        self.assertEquals(len(clusters_from_db), 1)
        cluster = clusters_from_db[0]
        self.assertEquals(cluster.nodes.all()[0].id, self.nodes[0].id)
        self.assertEquals(len(cluster.release.networks.all()), 3)
        # test delete
        resp = self.client.delete(
            reverse('cluster_handler', kwargs={'cluster_id': cluster.id}),
            "",
            "application/json"
        )
        self.assertEquals(resp.status_code, 204)

    def test_cluster_update(self):
        updated_name = 'Updated cluster'
        clusters_before = len(Cluster.objects.all())

        resp = self.client.put(
            reverse('cluster_handler',
                    kwargs={'cluster_id': self.clusters[0].id}),
            json.dumps({'name': updated_name}),
            "application/json"
        )
        self.assertEquals(resp.status_code, 200)

        clusters_from_db = Cluster.objects.filter(name=updated_name)
        self.assertEquals(len(clusters_from_db), 1)
        self.assertEquals(clusters_from_db[0].name, updated_name)

        clusters_after = len(Cluster.objects.all())
        self.assertEquals(clusters_before, clusters_after)

    def test_cluster_node_list_update(self):
        resp = self.client.put(
            reverse('cluster_handler', kwargs={'cluster_id': 1}),
            json.dumps({'nodes': [self.nodes[0].id]}),
            "application/json"
        )
        self.assertEquals(resp.status_code, 200)
        nodes_from_db = Node.objects.filter(cluster_id=1)
        self.assertEquals(len(nodes_from_db), 1)
        self.assertEquals(nodes_from_db[0].id, self.nodes[0].id)

        resp = self.client.put(
            reverse('cluster_handler', kwargs={'cluster_id': 1}),
            json.dumps({'nodes': [self.nodes[1].id]}),
            "application/json"
        )
        self.assertEquals(resp.status_code, 200)
        nodes_from_db = Node.objects.filter(cluster_id=1)
        self.assertEquals(len(nodes_from_db), 1)
        self.assertEquals(nodes_from_db[0].id, self.nodes[1].id)

    def test_node_creation(self):
        node_id = '080000000003'

        resp = self.client.post(
            reverse('node_collection_handler'),
            json.dumps({'id': node_id}),
            "application/json")
        self.assertEquals(resp.status_code, 200)

        nodes_from_db = Node.objects.filter(id=node_id)
        self.assertEquals(len(nodes_from_db), 1)

        # test delete
        resp = self.client.delete(
            reverse('node_handler', kwargs={'node_id': node_id}),
            "",
            "application/json"
        )
        self.assertEquals(resp.status_code, 204)

    def test_node_creation_using_put(self):
        node_id = '080000000002'

        resp = self.client.put(
            reverse('node_handler', kwargs={'node_id': node_id}),
            json.dumps({}),
            "application/json")
        self.assertEquals(resp.status_code, 200)

        nodes_from_db = Node.objects.filter(id=node_id)
        self.assertEquals(len(nodes_from_db), 1)

    def test_node_valid_metadata_gets_updated(self):
        resp = self.client.put(self.node_url,
                               json.dumps({'metadata': self.new_meta}),
                               "application/json")
        self.assertEquals(resp.status_code, 200)

        nodes_from_db = Node.objects.filter(id=self.nodes[0].id)
        self.assertEquals(len(nodes_from_db), 1)
        self.assertEquals(nodes_from_db[0].metadata, self.new_meta)

    def test_node_valid_status_gets_updated(self):
        params = {'status': 'error'}
        resp = self.client.put(self.node_url, json.dumps(params),
                "application/json")
        self.assertEquals(resp.status_code, 200)

    def test_node_valid_list_of_new_roles_gets_updated(self):
        resp = self.client.put(self.node_url,
            json.dumps({
                'new_roles': [self.roles[1].id],
                'redeployment_needed': True
            }), "application/json"
        )
        self.assertEquals(resp.status_code, 200)

        node_from_db = Node.objects.get(id=self.nodes[0].id)
        self.assertEquals(node_from_db.redeployment_needed, True)
        self.assertEquals(len(node_from_db.roles.all()), 1)
        self.assertEquals(len(node_from_db.new_roles.all()), 1)
        self.assertEquals(node_from_db.new_roles.all()[0].id,
                          self.roles[1].id)

    def test_put_returns_400_if_no_body(self):
        resp = self.client.put(self.node_url, None, "application/json")
        self.assertEquals(resp.status_code, 400)

    def test_put_returns_400_if_wrong_content_type(self):
        params = {'metadata': self.meta_json}
        resp = self.client.put(self.node_url, json.dumps(params), "plain/text")
        self.assertEquals(resp.status_code, 400)

    def test_put_returns_400_if_wrong_status(self):
        params = {'status': 'invalid_status'}
        resp = self.client.put(self.node_url, json.dumps(params),
                "application/json")
        self.assertEquals(resp.status_code, 400)

    def test_put_returns_400_if_no_block_device_attr(self):
        old_meta = self.nodes[0].metadata
        new_meta = self.new_meta.copy()
        del new_meta['block_device']
        resp = self.client.put(self.node_url,
                               json.dumps({'metadata': new_meta}),
                               "application/json")
        self.assertEquals(resp.status_code, 400)

        node_from_db = Node.objects.get(id=self.nodes[0].id)
        self.assertEquals(node_from_db.metadata, old_meta)

    def test_put_returns_400_if_no_interfaces_attr(self):
        old_meta = self.nodes[0].metadata
        new_meta = self.new_meta.copy()
        del new_meta['interfaces']
        resp = self.client.put(self.node_url,
                               json.dumps({'metadata': new_meta}),
                               "application/json")
        self.assertEquals(resp.status_code, 400)

        node_from_db = Node.objects.get(id=self.nodes[0].id)
        self.assertEquals(node_from_db.metadata, old_meta)

    def test_put_returns_400_if_interfaces_empty(self):
        old_meta = self.nodes[0].metadata
        new_meta = self.new_meta.copy()
        new_meta['interfaces'] = ""
        resp = self.client.put(self.node_url,
                               json.dumps({'metadata': new_meta}),
                               "application/json")
        self.assertEquals(resp.status_code, 400)

        node_from_db = Node.objects.get(id=self.nodes[0].id)
        self.assertEquals(node_from_db.metadata, old_meta)

    def test_put_returns_400_if_no_cpu_attr(self):
        old_meta = self.nodes[0].metadata
        new_meta = self.new_meta.copy()
        del new_meta['cpu']
        resp = self.client.put(self.node_url,
                               json.dumps({'metadata': new_meta}),
                               "application/json")
        self.assertEquals(resp.status_code, 400)

        node_from_db = Node.objects.get(id=self.nodes[0].id)
        self.assertEquals(node_from_db.metadata, old_meta)

    def test_put_returns_400_if_no_memory_attr(self):
        old_meta = self.nodes[0].metadata
        new_meta = self.new_meta.copy()
        del new_meta['memory']
        resp = self.client.put(self.node_url,
                               json.dumps({'metadata': new_meta}),
                               "application/json")
        self.assertEquals(resp.status_code, 400)

        node_from_db = Node.objects.get(id=self.nodes[0].id)
        self.assertEquals(node_from_db.metadata, old_meta)

    # (mihgen): Disabled - we don't have attributes anymore
    #def test_attribute_create(self):
        #resp = self.client.put(
            #reverse('attribute_collection_handler'),
            #json.dumps({
                #'attribute': {'a': 'av'},
                #'cookbook': 'cook_name',
                #'version': '0.1',
            #}), "application/json"
        #)
        #self.assertEquals(resp.status_code, 200)
        #self.assertEquals(resp.content, '1')

    #def test_attribute_update(self):
        #resp = self.client.put(
            #reverse('attribute_collection_handler'),
            #json.dumps({
                #'attribute': {'a': 'b'},
                #'cookbook': 'cook',
                #'version': '0.1',
            #}), "application/json"
        #)
        #self.assertEquals(resp.status_code, 200)
        #self.assertEquals(resp.content, '1')
        #resp = self.client.put(
            #reverse('attribute_collection_handler'),
            #json.dumps({
                #'attribute': {'a': 'new'},
                #'cookbook': 'cook',
                #'version': '0.1',
            #}), "application/json"
        #)
        #self.assertEquals(resp.status_code, 200)
        #self.assertEquals(resp.content, '1')
        #attrs = Attribute.objects.all()
        #self.assertEquals(len(attrs), 1)
        #self.assertEquals(attrs[0].attribute, {'a': 'new'})

    def test_role_create(self):
        role_name = 'My role 3'
        role_release = self.releases[0].id
        role_components = [c.name for c in self.com]
        resp = self.client.post(
            reverse('role_collection_handler'),
            json.dumps({
                'name': role_name,
                'release': role_release,
                'components': role_components
            }),
            "application/json"
        )
        self.assertEquals(resp.status_code, 200)

        roles_from_db = Role.objects.filter(name=role_name)
        self.assertEquals(len(roles_from_db), 1)
        components = [c.name for c in roles_from_db[0].components.all()]
        self.assertEquals(set(role_components), set(components))

    @mock.patch('nailgun.tasks.deploy_cluster', celery.task.task(lambda: True))
    def test_jsons_created_for_chef_solo(self):
        url = reverse('cluster_changes_handler', kwargs={'cluster_id': 1})
        resp = self.client.put(url)

        self.assertEquals(resp.status_code, 202)
        resp_json = json.loads(resp.content)
        self.assertEquals(len(resp_json['task_id']), 36)
        self.assertFalse(resp_json.get('error'))

    def test_release_create(self):
        release_name = "OpenStack"
        release_version = "1.0.0"
        release_description = "This is test release"
        release_roles = [{
            "name": "compute",
            "recipes": [
                "nova::compute@0.1.0",
                "nova::monitor@0.1.0"
            ]
          }, {
            "name": "controller",
            "recipes": [
                "cookbook::recipe@2.1"
            ]
          }
        ]
        resp = self.client.post(
            reverse('release_collection_handler'),
            json.dumps({
                'name': release_name,
                'version': release_version,
                'description': release_description,
                'roles': release_roles,
                'networks_metadata': [
                    {"name": "floating", "access": "public"},
                    {"name": "fixed", "access": "private"},
                    {"name": "storage", "access": "private"}
                ]
            }),
            "application/json"
        )
        self.assertEquals(resp.status_code, 200)

        # test duplicate release
        resp = self.client.post(
            reverse('release_collection_handler'),
            json.dumps({
                'name': release_name,
                'version': release_version,
                'description': release_description,
                'roles': release_roles,
                'networks_metadata': [
                    {"name": "fixed", "access": "private"}
                ]
            }),
            "application/json"
        )
        self.assertEquals(resp.status_code, 409)

        release_from_db = Release.objects.filter(
            name=release_name,
            version=release_version,
            description=release_description
        )
        self.assertEquals(len(release_from_db), 1)

        roles = []
        for rl in release_from_db[0].roles.all():
            roles.append({
                'name': rl.name,
                'recipes': [i.recipe for i in rl.recipes.all()]
            })
        for a, b in zip(sorted(roles), sorted(release_roles)):
            self.assertEquals(a, b)

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
        resp = self.client.post(
            reverse('network_collection_handler'),
            json.dumps(network_data),
            "application/json"
        )
        self.assertEquals(resp.status_code, 200)
        resp = self.client.post(
            reverse('network_collection_handler'),
            json.dumps(network_data),
            "application/json"
        )
        self.assertEquals(resp.status_code, 409)
        network_data["network"] = "test_fail"
        resp = self.client.post(
            reverse('network_collection_handler'),
            json.dumps(network_data),
            "application/json"
        )
        self.assertEqual(resp.status_code, 400)
