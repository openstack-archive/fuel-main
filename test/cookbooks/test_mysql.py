from . import CookbookTestCase
from devops.helpers import tcp_ping

class TestMysql(CookbookTestCase):
    cookbooks = ['mysql']

    mysql_port = 3306

    @classmethod
    def setUpState(klass):
        klass.chef_solo({
            'recipes': ['mysql::server'],
            'mysql': {
                'port': klass.mysql_port
            }
        })

    def test_mysql_deploy(self):
        assert tcp_ping(self.ip, self.mysql_port)

