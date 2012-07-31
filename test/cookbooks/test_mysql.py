import os
import simplejson as json
from unittest import TestCase
from nose.tools import eq_

from integration.helpers import HTTPClient, SSHClient
from . import ci


class TestMysql(TestCase):

    def setUp(self):
        self.ip = ci.environment.node['cookbooks'].ip_address
        self.cookbooks_dir = os.path.join(os.path.dirname(
                os.path.abspath(__file__)),
                "..", "..", "cooks", "cookbooks")
        self.remote = SSHClient()
        self.remote.connect_ssh(str(self.ip), "root", "r00tme")
        self.remote.mkdir("/opt/os-cookbooks/")
        solo_rb = """file_cache_path "/tmp/chef"
cookbook_path "/opt/os-cookbooks"
"""
        with open('/tmp/solo.rb', 'w') as f:
            f.write(solo_rb)
        self.remote.scp('/tmp/solo.rb', '/tmp/solo.rb')

    def test_mysql_deploy(self):
        self.remote.scp_d(self.cookbooks_dir + "/mysql", "/opt/os-cookbooks/")
        mysql_solo = {'recipes': ["mysql::server"]}
        with open('/tmp/mysql_solo.json', 'w') as f:
            f.write(json.dumps(mysql_solo))
        self.remote.scp('/tmp/mysql_solo.json', '/tmp/mysql_solo.json')

        res = self.remote.execute(
                "chef-solo -l debug -c /tmp/solo.rb -j /tmp/mysql_solo.json")
        print "*******************STDOUT*******************"
        for line in res['stdout']:
            print line
        print "*******************STDERR*******************"
        for line in res['stderr']:
            print line
        eq_(res['exit_status'], 0)
