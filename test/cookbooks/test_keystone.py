from . import CookbookTestCase
from devops.helpers import tcp_ping
from integration.helpers import HTTPClient
import simplejson as json

class TestKeystone(CookbookTestCase):
    cookbooks = ['chef-resource-groups', 'mysql', 'database', 'keystone']

    def test_keystone(self):
        mysql_port = 3306
        keystone_admin_port  = 37376
        keystone_public_port = 5000

        self.chef_solo({
            'run_list': ['recipe[mysql::server]', 'recipe[keystone::server]'],
            'mysql': {
                'port': mysql_port,
                'db_maker_password': 'secret'
            },
            'keystone': {
                'admin_port': keystone_admin_port,
                'public_port': keystone_public_port,

                'admin_url': "http://%s:%d" % (self.ip, keystone_admin_port),
                'public_url': "http://%s:%d" % (self.ip, keystone_public_port),
                'internal_url': "http://%s:%d" % (self.ip, keystone_public_port),
            },
            'services': {
                'keystone': {
                    'endpoints': {
                        'mysql': {
                            'host': str(self.ip),
                            'port': mysql_port,
                            'username': 'db_maker',
                            'password': 'secret'
                        }
                    }
                }
            }
        })

        assert tcp_ping(self.ip, keystone_public_port)

        http = HTTPClient()

        keystone_url = "http://%s:%d" % (self.ip, keystone_admin_port)

        services = json.loads(http.get(keystone_url + "/v2.0/OS-KSADM/services"))['OS-KSADM:services']
        keystone_service = None
        for service in services:
            if service['name'] == 'keystone':
                keystone_service = service
                break

        assert keystone_service, "Keystone service is not registered"
        assert keystone_service['type'] == 'identity', \
                "Keystone service has incorrect type ('%s' instead of 'identity')" % keystone_service['type']

