import simplejson as json
from django import http
from django.test import TestCase
from django.core.urlresolvers import reverse

from nailgun.models import Environment, Node, Cookbook, Role


class TestHandlers(TestCase):

    def setUp(self):
        self.request = http.HttpRequest()
        self.old_meta = {'block_device': 'value',
                         'interfaces': 'val2',
                         'cpu': 'asf',
                         'memory': 'sd'
                        }
        self.another_environment = Environment(id=2,
                name='Another environment')
        self.another_environment.save()

        self.node_name = "test.server.com"

        self.node = Node(id="080000000001",
                    environment_id=1,
                    name=self.node_name,
                    metadata=self.old_meta)
        self.node.save()

        self.cook = Cookbook()
        self.cook.name = 'cookbook'
        self.cook.version = '1.01.1'
        self.cook.save()

        self.role = Role()
        self.role.cookbook = self.cook
        self.role.name = "My role"
        self.role.save()

        self.another_role = Role()
        self.another_role.cookbook = self.cook
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
        self.another_environment.delete()
        self.node.delete()
        self.role.delete()
        self.another_role.delete()
        self.cook.delete()

    def test_environment_creation(self):
        yet_another_environment_name = 'Yet another environment'
        resp = self.client.post(
            reverse('environment_collection_handler'),
            json.dumps({'name': yet_another_environment_name}),
            "application/json"
        )
        self.assertEquals(resp.status_code, 200)

        environments_from_db = Environment.objects.filter(
            name=yet_another_environment_name
        )
        self.assertEquals(len(environments_from_db), 1)

    def test_node_creation(self):
        node_with_env_id = '080000000001'
        node_without_env_id = '080000000002'

        resp = self.client.post(
            reverse('node_collection_handler'),
            json.dumps({
                'id': node_with_env_id,
                'environment_id': 1,
            }),
            "application/json")
        self.assertEquals(resp.status_code, 200)

        resp = self.client.post(
            reverse('node_collection_handler'),
            json.dumps({'id': node_without_env_id}),
            "application/json")
        self.assertEquals(resp.status_code, 200)

        nodes_from_db = Node.objects.filter(id__in=[node_with_env_id,
                                                      node_without_env_id])
        self.assertEquals(len(nodes_from_db), 2)

    def test_node_environment_update(self):
        resp = self.client.put(
            reverse('node_handler', kwargs={'node_id': self.node.id}),
            json.dumps({'environment_id': 2}),
            "application/json")
        self.assertEquals(resp.status_code, 400)

        resp = self.client.put(
            reverse('node_handler', kwargs={'node_id': self.node.id}),
            json.dumps({'environment_id': None}),
            "application/json")
        self.assertEquals(resp.status_code, 200)

        resp = self.client.put(
            reverse('node_handler', kwargs={'node_id': self.node.id}),
            json.dumps({'environment_id': 1}),
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

    def test_put_on_nodes_does_not_modify_roles_list(self):
        resp = self.client.put(self.node_url, json.dumps(self.new_meta),
                "application/json")

        nodes_from_db = Node.objects.filter(id=self.node.id)
        self.assertEquals(nodes_from_db[0].roles.all()[0].id, 1)

    # Tests for RoleHandler
    def test_can_get_list_of_roles_for_node(self):
        resp = self.client.get(self.node_url + '/roles')
        self.assertEquals(json.loads(resp.content)[0]['id'], 1)

    def test_list_of_roles_gets_updated_via_post(self):
        url = self.node_url + '/roles/' + str(self.another_role.id)
        resp = self.client.post(url, '', "plain/text")
        self.assertEquals(resp.status_code, 200)

        resp = self.client.post(url, '', "plain/text")
        self.assertEquals(resp.status_code, 409)

        roles_from_db = Role.objects.all()
        nodes_from_db = Node.objects.filter(id=self.node.id)
        self.assertEquals(nodes_from_db[0].roles.all()[0].id,
                self.role.id)
        self.assertEquals(nodes_from_db[0].roles.all()[1].id,
                self.another_role.id)

    def test_cookbook_create(self):
        cook_name = 'new cookbook'
        cook_ver = '0.1.0'
        resp = self.client.post(
            reverse('cookbook_collection_handler'),
            json.dumps({'name': cook_name, 'version': cook_ver}),
            "application/json"
        )
        self.assertEquals(resp.status_code, 200)

        cooks_from_db = Cookbook.objects.filter(
            name=cook_name
        )
        self.assertEquals(len(cooks_from_db), 1)
        self.assertEquals(cooks_from_db[0].version, cook_ver)


    #def test_jsons_created_for_chef_solo(self):
        #resp = self.client.post('/api/environments/1/chef-config/')
        #print resp.content
        #raise
