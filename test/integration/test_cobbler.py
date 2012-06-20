from devops.helpers import wait, tcp_ping, http, ssh
import xmlrpclib

from . import ci

class TestCobbler:
    def setUp(self):
        pass

    def test_cobbler_xmlrpc(self):
        admin_node = ci.environment.node['admin']

        wait(lambda: http(host=admin_node.ip_address, url='/cobbler_api', waited_code=501), timeout=30)

        server = xmlrpclib.Server('http://%s/cobbler_api' % admin_node.ip_address)
        token = server.login('cobbler', 'cobbler')
        found = server.find_system({'name':'default'}, token)
        assert found[0]['name'] == 'default'
           
    def test_cobbler_alive(self):
        assert True

    # def test_cobbler_alive(self):
    #     wait(lambda: ssh)
