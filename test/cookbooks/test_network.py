from . import CookbookTestCase
from devops.helpers import tcp_ping

class TestNetworkCreateInterfaces(CookbookTestCase):
    cookbooks = ['network']

    @classmethod
    def setUpState(klass):
        klass.chef_solo({
            'recipes': ['network::create_interfaces'],
            'networks': {
                'first': {'device': 'eth0',
                    'vlan_id': 111,
                    'address': '192.168.111.10',
                    'netmask': '255.255.255.0'
                    },
                'second': {'device': 'eth0',
                    'vlan_id': 222,
                    'address': '192.168.222.10',
                    'netmask': '255.255.255.0'
                    }
            },
        })

    def test_network_create_interface(self):
        cmd = 'ifconfig | grep "^eth0\.[0-9][0-9]*"|wc -l'
        error_msg = 'There must be two eth0 subinterfaces.'
        run_result = self.remote.execute(cmd)
        assert run_result['stdout'][0].strip() == '2', error_msg
