import simplejson as json
from django import http
from django.test import TestCase
from django.db.models import Model
from django.core.urlresolvers import reverse, NoReverseMatch

from piston.emitters import Emitter

from nailgun.models import Cluster, Node, Recipe, Role, Release
from nailgun.api import urls as api_urls


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
        self.old_meta = {'block_device': 'value',
                         'interfaces': 'val2',
                         'cpu': 'asf',
                         'memory': 'sd'
                        }
        self.another_cluster = Cluster(id=2,
                name='Another cluster')
        self.another_cluster.save()

        self.node_name = "test.server.com"

        self.node = Node(id="080000000001",
                    cluster_id=1,
                    name=self.node_name,
                    ip="127.0.0.1",
                    metadata=self.old_meta)
        self.node.save()

        self.another_node = Node(
                    id="080000000000",
                    name="test2.server.com",
                    ip="127.0.0.2",
                    metadata=self.old_meta)
        self.another_node.save()

        self.recipe = Recipe()
        self.recipe.recipe = 'cookbook::recipe@2.1'
        self.recipe.save()
        self.second_recipe = Recipe()
        self.second_recipe.recipe = 'nova::compute@0.1.0'
        self.second_recipe.save()
        self.third_recipe = Recipe()
        self.third_recipe.recipe = 'nova::monitor@0.1.0'
        self.third_recipe.save()

        self.role = Role()
        self.role.save()
        self.role.recipes.add(self.recipe)
        self.role.name = "My role"
        self.role.save()

        self.another_role = Role()
        self.another_role.save()
        self.another_role.recipes.add(self.recipe)
        self.another_role.name = "My role 2"
        self.another_role.save()

        self.node.roles = [self.role]
        self.node.save()
        self.node_url = reverse('node_handler',
                                kwargs={'node_id': self.node.id})

        self.new_meta = {'block_device': 'new-val',
                         'interfaces': 'd',
                         'cpu': 'u',
                         'memory': 'a'
                        }
        self.meta_json = json.dumps(self.new_meta)

    def tearDown(self):
        self.another_cluster.delete()
        self.node.delete()
        self.role.delete()
        self.another_role.delete()
        self.recipe.delete()
        self.second_recipe.delete()
        self.third_recipe.delete()

    def test_all_api_urls_500(self):
        test_urls = {}
        for pattern in api_urls.urlpatterns:
            test_urls[pattern.name] = pattern.callback.handler.allowed_methods

        url_ids = {
            'cluster_handler': {'cluster_id': 1},
            'node_handler': {'node_id': 'A' * 12},
            #'task_handler': {'task_id': 'a' * 36},
            'release_handler': {'release_id': 1},
            'role_handler': {'role_id': 1},
            'node_role_available': {'node_id': 'A' * 12, 'role_id': 1},
            'recipe_handler': {'recipe_id': 1}
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
                print test_url
                print resp.content
                self.assertNotEqual(str(resp.status_code)[0], '5')

    def test_cluster_creation(self):
        yet_another_cluster_name = 'Yet another cluster'
        resp = self.client.post(
            reverse('cluster_collection_handler'),
            json.dumps({'name': yet_another_cluster_name}),
            "application/json"
        )
        self.assertEquals(resp.status_code, 200)

        clusters_from_db = Cluster.objects.filter(
            name=yet_another_cluster_name
        )
        self.assertEquals(len(clusters_from_db), 1)

    def test_cluster_update(self):
        updated_name = 'Updated cluster'
        clusters_before = len(Cluster.objects.all())

        resp = self.client.put(
            reverse('cluster_handler',
                    kwargs={'cluster_id': self.another_cluster.id}),
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
            json.dumps({'nodes': [self.node.id]}),
            "application/json"
        )
        self.assertEquals(resp.status_code, 200)
        nodes_from_db = Node.objects.filter(cluster_id=1)
        self.assertEquals(len(nodes_from_db), 1)
        self.assertEquals(nodes_from_db[0].id, self.node.id)

        resp = self.client.put(
            reverse('cluster_handler', kwargs={'cluster_id': 1}),
            json.dumps({'nodes': [self.another_node.id]}),
            "application/json"
        )
        self.assertEquals(resp.status_code, 200)
        nodes_from_db = Node.objects.filter(cluster_id=1)
        self.assertEquals(len(nodes_from_db), 1)
        self.assertEquals(nodes_from_db[0].id, self.another_node.id)

    def test_node_creation(self):
        node_with_cluster_id = '080000000002'
        node_without_cluster_id = '080000000003'

        resp = self.client.post(
            reverse('node_collection_handler'),
            json.dumps({
                'id': node_with_cluster_id,
                'cluster_id': 1,
            }),
            "application/json")
        self.assertEquals(resp.status_code, 200)

        resp = self.client.post(
            reverse('node_collection_handler'),
            json.dumps({'id': node_without_cluster_id}),
            "application/json")
        self.assertEquals(resp.status_code, 200)

        nodes_from_db = Node.objects.filter(id__in=[node_with_cluster_id,
                                                      node_without_cluster_id])
        self.assertEquals(len(nodes_from_db), 2)

    def test_node_creation_using_put(self):
        node_id = '080000000002'

        resp = self.client.put(
            reverse('node_handler', kwargs={'node_id': node_id}),
            json.dumps({}),
            "application/json")
        self.assertEquals(resp.status_code, 200)

        nodes_from_db = Node.objects.filter(id=node_id)
        self.assertEquals(len(nodes_from_db), 1)

    def test_node_cluster_update(self):
        resp = self.client.put(
            reverse('node_handler', kwargs={'node_id': self.node.id}),
            json.dumps({'cluster_id': 2}),
            "application/json")
        self.assertEquals(resp.status_code, 400)

        resp = self.client.put(
            reverse('node_handler', kwargs={'node_id': self.node.id}),
            json.dumps({'cluster_id': None}),
            "application/json")
        self.assertEquals(resp.status_code, 200)

        resp = self.client.put(
            reverse('node_handler', kwargs={'node_id': self.node.id}),
            json.dumps({'cluster_id': 1}),
            "application/json")
        self.assertEquals(resp.status_code, 200)

    def test_node_valid_metadata_gets_updated(self):
        resp = self.client.put(self.node_url,
                               json.dumps({'metadata': self.new_meta}),
                               "application/json")
        self.assertEquals(resp.status_code, 200)

        nodes_from_db = Node.objects.filter(id=self.node.id)
        self.assertEquals(len(nodes_from_db), 1)
        self.assertEquals(nodes_from_db[0].metadata, self.new_meta)

    def test_node_valid_status_gets_updated(self):
        params = {'status': 'offline'}
        resp = self.client.put(self.node_url, json.dumps(params),
                "application/json")
        self.assertEquals(resp.status_code, 200)

    def test_node_valid_list_of_roles_gets_updated(self):
        resp = self.client.put(self.node_url,
            json.dumps({'roles': [self.another_role.id]}),
            "application/json")
        self.assertEquals(resp.status_code, 200)

        node_from_db = Node.objects.get(id=self.node.id)
        self.assertEquals(len(node_from_db.roles.all()), 1)
        self.assertEquals(node_from_db.roles.all()[0].id, self.another_role.id)

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
        meta = self.new_meta.copy()
        del meta['block_device']
        resp = self.client.put(self.node_url,
                               json.dumps({'metadata': meta}),
                               "application/json")
        self.assertEquals(resp.status_code, 400)

        nodes_from_db = Node.objects.filter(id=self.node.id)
        self.assertEquals(len(nodes_from_db), 1)
        self.assertEquals(nodes_from_db[0].metadata, self.old_meta)

    def test_put_returns_400_if_no_interfaces_attr(self):
        meta = self.new_meta.copy()
        del meta['interfaces']
        resp = self.client.put(self.node_url,
                               json.dumps({'metadata': meta}),
                               "application/json")
        self.assertEquals(resp.status_code, 400)

        nodes_from_db = Node.objects.filter(id=self.node.id)
        self.assertEquals(len(nodes_from_db), 1)
        self.assertEquals(nodes_from_db[0].metadata, self.old_meta)

    def test_put_returns_400_if_interfaces_empty(self):
        meta = self.new_meta.copy()
        meta['interfaces'] = ""
        resp = self.client.put(self.node_url,
                               json.dumps({'metadata': meta}),
                               "application/json")
        self.assertEquals(resp.status_code, 400)

        nodes_from_db = Node.objects.filter(id=self.node.id)
        self.assertEquals(len(nodes_from_db), 1)
        self.assertEquals(nodes_from_db[0].metadata, self.old_meta)

    def test_put_returns_400_if_no_cpu_attr(self):
        meta = self.new_meta.copy()
        del meta['cpu']
        resp = self.client.put(self.node_url,
                               json.dumps({'metadata': meta}),
                               "application/json")
        self.assertEquals(resp.status_code, 400)

        nodes_from_db = Node.objects.filter(id=self.node.id)
        self.assertEquals(len(nodes_from_db), 1)
        self.assertEquals(nodes_from_db[0].metadata, self.old_meta)

    def test_put_returns_400_if_no_memory_attr(self):
        meta = self.new_meta.copy()
        del meta['memory']
        resp = self.client.put(self.node_url,
                               json.dumps({'metadata': meta}),
                               "application/json")
        self.assertEquals(resp.status_code, 400)

        nodes_from_db = Node.objects.filter(id=self.node.id)
        self.assertEquals(len(nodes_from_db), 1)
        self.assertEquals(nodes_from_db[0].metadata, self.old_meta)

    def test_recipe_create(self):
        recipe = 'cookbook::recipe@0.1.0'
        resp = self.client.post(
            reverse('recipe_collection_handler'),
            json.dumps({
                'recipe': recipe
            }),
            "application/json"
        )
        self.assertEquals(resp.status_code, 200)

        # test duplicate
        resp = self.client.post(
            reverse('recipe_collection_handler'),
            json.dumps({
                'recipe': recipe
            }),
            "application/json"
        )
        self.assertEquals(resp.status_code, 409)

        # test wrong format
        resp = self.client.post(
            reverse('recipe_collection_handler'),
            json.dumps({
                'recipe': 'ololo::onotole'
            }),
            "application/json"
        )
        self.assertEquals(resp.status_code, 400)

        recipe_from_db = Recipe.objects.filter(recipe=recipe)
        self.assertEquals(len(recipe_from_db), 1)

    def test_role_create(self):
        role_name = 'My role 3'
        role_recipes = [
            'nova::compute@0.1.0',
            'nova::monitor@0.1.0'
        ]
        resp = self.client.post(
            reverse('role_collection_handler'),
            json.dumps({
                'name': role_name,
                'recipes': role_recipes
            }),
            "application/json"
        )
        self.assertEquals(resp.status_code, 200)

        roles_from_db = Role.objects.filter(name=role_name)
        self.assertEquals(len(roles_from_db), 1)
        recipes = [r.recipe for r in roles_from_db[0].recipes.all()]
        self.assertEquals(set(role_recipes), set(recipes))

    def test_jsons_created_for_chef_solo(self):
        url = reverse('config_handler', kwargs={'cluster_id': 1})
        resp = self.client.post(url)
        print resp.content
        self.assertEquals(resp.status_code, 202)
        resp_json = json.loads(resp.content)
        self.assertEquals(len(resp_json['task_id']), 36)

    def test_validate_node_role_available(self):
        url = reverse('node_role_available', kwargs={
            'node_id': '080000000001',
            'role_id': '1'
        })
        resp = self.client.get(url)
        self.assertEquals(resp.status_code, 200)

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
                'roles': release_roles
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
                'roles': release_roles
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
