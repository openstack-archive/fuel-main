from . import CookbookTestCase
from openstack_common import OpenstackCommon

from devops.helpers import tcp_ping
from integration.helpers import HTTPClient
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

    def test_public_port_open(self):
        assert tcp_ping(self.ip, self.keystone_public_port)

    def test_keystone_identity_service_registered(self):
        keystone_url = "http://%s:%d" % (self.ip, self.keystone_admin_port)

        http = HTTPClient()
        services = json.loads(http.get(keystone_url + "/v2.0/OS-KSADM/services"))['OS-KSADM:services']

        keystone_service = find(lambda service: service['name'] == 'keystone', services)

        assert keystone_service, "Keystone service is not registered"
        assert keystone_service['type'] == 'identity', \
                "Keystone service has incorrect type ('%s' instead of 'identity')" % keystone_service['type']

