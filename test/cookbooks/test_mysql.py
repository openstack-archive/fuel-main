import os

from unittest import TestCase

from integration.helpers import HTTPClient, SSHClient
from . import ci

class TestMysql(TestCase):
    def setUp(self):
        self.ip = ci.environment.node['cookbooks'].ip_address
        self.cookbooks_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), \
                "..", "..", "cooks", "cookbooks")
        self.remote = SSHClient()
        self.remote.connect_ssh(str(self.ip), "root", "r00tme")

    def test_mysql_deploy(self):
        self.remote.mkdir("/opt/os-cookbooks/")
        self.remote.scp_d(self.cookbooks_dir + "/mysql", "/opt/os-cookbooks/")
        self.remote.exec_cmd("chef-solo")
