from . import CookbookTestCase
from devops.helpers import tcp_ping

class TestFirewallEnable(CookbookTestCase):
    cookbooks = ['firewall','rabbitmq']
    rabbitmq_port = 5672

    @classmethod
    def setUpState(klass):
        klass.chef_solo({
            'recipes': ['rabbitmq', 'firewall::enable'],
            'rabbitmq': {
                'port': klass.rabbitmq_port
            }
        })

    def test_firewall_enable(self):
        msg = 'Firewall disabled or port %s allowed.' % (self.rabbitmq_port,)
        assert not tcp_ping(self.ip, self.rabbitmq_port), msg

class TestFirewallDisable(CookbookTestCase):
    cookbooks = ['firewall', 'rabbitmq']
    rabbitmq_port = 5672

    @classmethod
    def setUpState(klass):
        klass.chef_solo({
            'recipes': ['rabbitmq', 'firewall::disable'],
            'rabbitmq': {
                'port': klass.rabbitmq_port
            }
        })

    def test_firewall_disable(self):
        msg = 'Firewall still enabled. No conection to RabbitMQ port.'
        assert tcp_ping(self.ip, self.rabbitmq_port), msg
