from . import CookbookTestCase
from openstack_common import OpenstackCommon

class TestGlanceRegistry(CookbookTestCase, OpenstackCommon):
    cookbooks = ['chef-resource-groups', 'database', 'keystone', 'glance']

    @classmethod
    def setUpState(klass):
        klass.setUpKeystone()
        klass.setUpGlanceRegistry(reuse_cached=False)

    def test_glance_registry(self):
        pass

