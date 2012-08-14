from . import CookbookTestCase
from openstack_common import OpenstackCommon

from devops.helpers import tcp_ping
import httplib
import os
import simplejson as json

def find(predicate, sequence):
    "Returns first element of sequence for which predicate is true or None"
    for item in sequence:
        if predicate(item):
            return item

    return None

class TestKeystone(CookbookTestCase, OpenstackCommon):
    cookbooks = ['chef-resource-groups', 'database', 'keystone']

    @classmethod
    def setUpState(klass):
        klass.setUpMysql()
        klass.setUpKeystone(reuse_cached=False)

    def keystone_data(self, url):
        conn = httplib.HTTPConnection(str(self.ip), self.keystone_admin_port)
        conn.request('GET', url, None, {'X-Auth-Token': self.keystone_admin_token})
        res = conn.getresponse()
        data = res.read()

        assert res.status in [200], \
            "Keystone request was expected to return code 200, but was %d (%s)\n%s" % (res.status, res.reason, data)

        return json.loads(data)

    def test_admin_port_open(self):
        assert tcp_ping(self.ip, self.keystone_admin_port)

    def test_public_port_open(self):
        assert tcp_ping(self.ip, self.keystone_public_port)

    def test_keystone_identity_service_registered(self):
        services = self.keystone_data('/v2.0/OS-KSADM/services')['OS-KSADM:services']
        keystone_service = find(lambda service: service['name'] == 'keystone', services)

        assert keystone_service, "Keystone service is not registered"
        assert keystone_service['type'] == 'identity', \
                "Keystone service has incorrect type ('%s' instead of 'identity')" % keystone_service['type']


    def _create_tenant(self, name, description=''):
        self.chef_run_recipe("""
            keystone_tenant '%(name)s' do
              connection :url => 'http://localhost:%(port)d',
                         :token => '%(token)s'
              description '%(description)s'
            end
        """ % {
            'name': name,
            'description': description,
            'port': self.keystone_admin_port,
            'token': self.keystone_admin_token
        })

    def _delete_tenant(self, name):
        self.chef_run_recipe("""
            keystone_tenant '%(name)s' do
              connection :url => 'http://localhost:%(port)d',
                         :token => '%(token)s'
              action :delete
            end
        """ % {
            'name': name,
            'port': self.keystone_admin_port,
            'token': self.keystone_admin_token
        })

    def test_tenant_creation(self):
        self._create_tenant('foo', 'Test tenant')

        tenants = self.keystone_data('/v2.0/tenants')['tenants']
        tenant = find(lambda tenant: tenant['name'] == 'foo', tenants)

        assert tenant, "Tenant wasn't created"
        self.assertEqual('Test tenant', tenant['description'])
        self.assertEqual(True, tenant['enabled'])

    def test_tenant_creation_doesnt_fail_if_tenant_already_do_exist(self):
        self._create_tenant('foo', 'Test tenant')
        self._create_tenant('foo', 'Test tenant')

        tenants = self.keystone_data('/v2.0/tenants')['tenants']
        tenant = find(lambda tenant: tenant['name'] == 'foo', tenants)

        assert tenant, "Tenant wasn't created"

    def test_tenant_deletion(self):
        self._create_tenant('foo')
        self._delete_tenant('foo')

        tenants = self.keystone_data('/v2.0/tenants')['tenants']
        tenant = find(lambda tenant: tenant['name'] == 'foo', tenants)

        assert tenant == None, "Tenant wasn't deleted"


    def test_tenant_deletion_doesnt_fail_if_tenant_do_not_exist(self):
        self._create_tenant('foo')
        self._delete_tenant('foo')
        self._delete_tenant('foo')


    def _create_role(self, name):
        self.chef_run_recipe("""
            keystone_role '%(name)s' do
              connection :url => 'http://localhost:%(port)d',
                         :token => '%(token)s'
            end
        """ % {
            'name': name,
            'port': self.keystone_admin_port,
            'token': self.keystone_admin_token
        })

    def _delete_role(self, name):
        self.chef_run_recipe("""
            keystone_role '%(name)s' do
              connection :url => 'http://localhost:%(port)d',
                         :token => '%(token)s'
              action :delete
            end
        """ % {
            'name': name,
            'port': self.keystone_admin_port,
            'token': self.keystone_admin_token
        })

    def test_role_creation(self):
        self._create_role('foo')

        roles = self.keystone_data('/v2.0/OS-KSADM/roles')['roles']
        role = find(lambda role: role['name'] == 'foo', roles)

        assert role, "Role wasn't created"

    def test_role_creation_doesnt_fail_if_role_do_exist(self):
        self._create_role('foo')
        self._create_role('foo')

    def test_role_deletion(self):
        self._create_role('foo')

        self._delete_role('foo')

        roles = self.keystone_data('/v2.0/OS-KSADM/roles')['roles']
        role = find(lambda role: role['name'] == 'foo', roles)

        assert role == None, "Role wasn't deleted"

    def test_role_deletion_doesnt_fail_if_role_do_not_exist(self):
        self._create_role('foo')

        self._delete_role('foo')

        roles = self.keystone_data('/v2.0/OS-KSADM/roles')['roles']
        role = find(lambda role: role['name'] == 'foo', roles)

        assert role == None, "Role wasn't deleted"

