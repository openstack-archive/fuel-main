from devops.helpers import wait, tcp_ping, http, ssh
import xmlrpclib

from . import ci

class TestCobbler:
    def setUp(self):
        self.ip = ci.environment.node['admin'].ip_address

    def test_cobbler_alive(self):
        wait(lambda: http(host=admin_node.ip_address, url='/cobbler_api', waited_code=501), timeout=60)
        server = xmlrpclib.Server('http://%s/cobbler_api' % self.ip)
        token = server.login('cobbler', 'cobbler')
        assert server.ping() == True

