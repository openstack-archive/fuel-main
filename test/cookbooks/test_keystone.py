from . import CookbookTestCase
from devops.helpers import tcp_ping
from integration.helpers import HTTPClient
import os
import simplejson as json

class TestKeystone(CookbookTestCase):
    cookbooks = ['chef-resource-groups', 'mysql', 'database', 'keystone']

    mysql_port = 3306

    keystone_admin_port  = 37376
    keystone_public_port = 5000


    @classmethod
    def setUpState(klass):
        klass.chef_solo({
            'recipes': ['mysql::server'],
            'mysql': {
                'port': klass.mysql_port,
                'db_maker_password': 'secret'
            },
        })


        klass.chef_solo({
            'recipes': ['keystone::server'],
            'keystone': {
                'admin_port': klass.keystone_admin_port,
                'public_port': klass.keystone_public_port,

                'admin_url': "http://%s:%d" % (klass.ip, klass.keystone_admin_port),
                'public_url': "http://%s:%d" % (klass.ip, klass.keystone_public_port),
                'internal_url': "http://%s:%d" % (klass.ip, klass.keystone_public_port),
            },
            'services': {
                'keystone': {
                    'endpoints': {
                        'mysql': {
                            'host': str(klass.ip),
                            'port': klass.mysql_port,
                            'username': 'db_maker',
                            'password': 'secret'
                        }
                    }
                }
            }
        })

    def test_public_port_open(self):
        assert tcp_ping(self.ip, self.keystone_public_port)

    def test_keystone_identity_service_registered(self):
        http = HTTPClient()

        keystone_url = "http://%s:%d" % (self.ip, self.keystone_admin_port)

        services = json.loads(http.get(keystone_url + "/v2.0/OS-KSADM/services"))['OS-KSADM:services']
        keystone_service = None
        for service in services:
            if service['name'] == 'keystone':
                keystone_service = service
                break

        assert keystone_service, "Keystone service is not registered"
        assert keystone_service['type'] == 'identity', \
                "Keystone service has incorrect type ('%s' instead of 'identity')" % keystone_service['type']

