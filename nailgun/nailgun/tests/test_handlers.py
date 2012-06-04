import simplejson as json
from django import http
from django.test import TestCase
from django.core.urlresolvers import reverse

from nailgun.models import Environment, Node, Cookbook, Role
from nailgun.tasks import create_chef_config


class TestHandlers(TestCase):

    def setUp(self):
        self.request = http.HttpRequest()
        self.old_meta = {'block_device': 'value',
                         'interfaces': 'val2',
                         'cpu': 'asf',
                         'memory': 'sd',
                         'ip': '192.168.124.185',
                         'mac': '08:00:27:99:8F:33',
                         'fqdn': 'test.server.com'
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
                         'memory': 'a',
                         'ip': '10.1.1.1',
                         'mac': '09:02:FB:AA:AB:AC',
                         'fqdn': 'new.com'
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

    def test_environment_update(self):
        updated_name = 'Updated environment'
        environments_before = len(Environment.objects.all())

        resp = self.client.put(
            reverse('environment_handler',
                    kwargs={'environment_id': self.another_environment.id}),
            json.dumps({'name': updated_name}),
            "application/json"
        )
        self.assertEquals(resp.status_code, 200)

        environments_from_db = Environment.objects.filter(name=updated_name)
        self.assertEquals(len(environments_from_db), 1)
        self.assertEquals(environments_from_db[0].name, updated_name)

        environments_after = len(Environment.objects.all())
        self.assertEquals(environments_before, environments_after)

    def test_node_creation(self):
        node_with_env_id = '080000000002'
        node_without_env_id = '080000000003'

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

    def test_node_creation_using_put(self):
        node_id = '080000000002'

        resp = self.client.put(
            reverse('node_handler', kwargs={'node_id': node_id}),
            json.dumps({}),
            "application/json")
        self.assertEquals(resp.status_code, 200)

        nodes_from_db = Node.objects.filter(id=node_id)
        self.assertEquals(len(nodes_from_db), 1)

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
        print resp.content
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

    def test_put_returns_400_if_ipaddress_empty(self):
        meta = self.new_meta.copy()
        meta['ip'] = ""
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

    def test_cookbook_create(self):
        cook_name = 'new cookbook'
        cook_ver = '0.1.0'
        resp = self.client.post(
            reverse('cookbook_collection_handler'),
            json.dumps({'name': cook_name, 'version': cook_ver}),
            "application/json"
        )
        self.assertEquals(resp.status_code, 200)

        cooks_from_db = Cookbook.objects.filter(name=cook_name)
        self.assertEquals(len(cooks_from_db), 1)
        self.assertEquals(cooks_from_db[0].version, cook_ver)

    def test_role_create(self):
        role_name = 'My role 3'

        resp = self.client.post(
            reverse('role_collection_handler'),
            json.dumps({'name': role_name, 'cookbook_id': self.cook.id}),
            "application/json"
        )
        self.assertEquals(resp.status_code, 200)

        roles_from_db = Role.objects.filter(name=role_name)
        self.assertEquals(len(roles_from_db), 1)
        self.assertEquals(roles_from_db[0].cookbook.id, self.cook.id)

    def test_jsons_created_for_chef_solo(self):
        url = reverse('config_handler', kwargs={'environment_id': 1})
        resp = self.client.post(url)
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
