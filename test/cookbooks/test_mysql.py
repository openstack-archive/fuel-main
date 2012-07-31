from . import CookbookTestCase
from devops.helpers import tcp_ping

class TestMysql(CookbookTestCase):
    cookbooks = ['mysql']

    def test_mysql_deploy(self):
        mysql_port = 3306

        self.chef_solo({
            'run_list': ['recipe[mysql::server]'],
            'mysql': {
                'port': mysql_port
            }
        })

        assert tcp_ping(self.ip, mysql_port)

