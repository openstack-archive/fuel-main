from . import CookbookTestCase
from devops.helpers import tcp_ping

class TestRabbitMQ(CookbookTestCase):
    cookbooks = ['rabbitmq']
    rabbitmq_port = 5672

    @classmethod
    def setUpState(klass):
        klass.chef_solo({
            'recipes': ['rabbitmq'],
            'rabbitmq': {
                'port': klass.rabbitmq_port
            }
        })

    def test_rabbitmq_deploy(self):
        assert tcp_ping(self.ip, self.rabbitmq_port), 'No conection to RabbitMQ port.'
