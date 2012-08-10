from . import CookbookTestCase
from devops.helpers import tcp_ping

class TestNTP(CookbookTestCase):
    cookbooks = ['ntp']

    @classmethod
    def setUpState(klass):
        klass.chef_solo({
            'recipes': ['ntp']
        })

    def test_is_ntp_running(self):
        cmd = 'ps aux|grep \'[ /]ntp\''
        error_msg = 'There is no NTP process in memory.'
        run_result = self.remote.execute(cmd)
        assert run_result['exit_code'] == 0, error_msg

