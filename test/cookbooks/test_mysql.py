from . import CookbookTestCase
from openstack_common import OpenstackCommon
from devops.helpers import tcp_ping

class TestMysql(CookbookTestCase, OpenstackCommon):
    cookbooks = ['mysql']

    @classmethod
    def setUpState(klass):
        klass.setUpMysql(reuse_cached=False)

    def test_mysql_deploy(self):
        assert tcp_ping(self.ip, self.mysql_port)

