from devops.helpers import wait, tcp_ping, http
import xmlrpclib

from . import ci

class TestCobbler:
    def setUp(self):
        wait(lambda: tcp_ping(ci.admin_node.ip_address, 22))

    def test_cobbler_alive(self):
        wait(lambda: http(host=ci.admin_node.ip_address, url='/cobbler_api', waited_code=501))
        server = xmlrpclib.Server('http://%s/cobbler_api' % ci.admin_node.ip_address)
        token = server.login('cobbler', 'cobbler')
        found = server.find_system({'name':'default'}, token)
        assert found[0]['name'] == 'default'
            
