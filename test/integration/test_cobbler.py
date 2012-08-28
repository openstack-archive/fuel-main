import logging
import xmlrpclib
from time import sleep



from devops.helpers import wait, tcp_ping, http, ssh
from integration.base import Base
from helpers import SSHClient



class TestCobbler(Base):
    def __init__(self, *args, **kwargs):
        super(TestCobbler, self).__init__(*args, **kwargs)
        self.remote = SSHClient()
        self.logpath = "/var/log/chef/solo.log"
        self.str_success = "Report handlers complete"


    def setUp(self):
        self.ip = self.get_admin_node_ip()


    def tearDown(self):
        pass


    def test_cobbler_alive(self):
        logging.info("Waiting for handlers to complete")

        self.remote.connect_ssh(str(self.ip), "ubuntu", "r00tme")
        count = 0
        while True:
            res = self.remote.execute("grep '%s' '%s'" % (self.str_success, self.logpath))
            count += 1
            if not res['exit_status']:
                break
            sleep(5)
            if count == 200:
                raise Exception("Chef handlers failed to complete")
        self.remote.disconnect()

        wait(lambda: http(host=self.ip, url='/cobbler_api', waited_code=501), timeout=60)
        server = xmlrpclib.Server('http://%s/cobbler_api' % self.ip)
        token = server.login('cobbler', 'cobbler')
        assert server.ping() == True
