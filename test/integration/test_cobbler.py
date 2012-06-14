from devops.helpers import wait, tcp_ping, http, ssh
import xmlrpclib

from . import ci

class TestCobbler:
    def setUp(self):
        pass

    def test_cobbler_xmlrpc(self):
        wait(lambda: http(host=ci.environment.node['admin'].ip_address, url='/cobbler_api', waited_code=501))
        server = xmlrpclib.Server('http://%s/cobbler_api' % ci.environment.node['admin'].ip_address)
        token = server.login('cobbler', 'cobbler')
        found = server.find_system({'name':'default'}, token)
        assert found[0]['name'] == 'default'
           
    def test_cobbler_alive(self):
        assert True

    # def test_cobbler_alive(self):
    #     wait(lambda: ssh)
