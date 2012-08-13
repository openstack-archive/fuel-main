from . import CookbookTestCase
from openstack_common import OpenstackCommon
from devops.helpers import tcp_ping, wait

class TestGlanceRegistry(CookbookTestCase, OpenstackCommon):
    cookbooks = ['chef-resource-groups', 'database', 'keystone', 'glance']

    @classmethod
    def setUpState(klass):
        klass.setUpKeystone()
        klass.setUpGlanceRegistry(reuse_cached=False)

    def test_glance_registry_port_open(self):
        assert tcp_ping(self.ip, self.glance_registry_port)


class TestGlanceApi(CookbookTestCase, OpenstackCommon):
    cookbooks = ['chef-resource-groups', 'database', 'keystone', 'glance']

    @classmethod
    def setUpState(klass):
        klass.setUpGlanceRegistry()
        klass.setUpGlanceApi(reuse_cached=False)

    def test_glance_api_port_open(self):
        assert tcp_ping(self.ip, self.glance_api_port)
