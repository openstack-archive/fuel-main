from . import CookbookTestCase
from devops.helpers import tcp_ping

class TestNovaRabbitMQ(CookbookTestCase):
    cookbooks = ['rabbitmq', 'nova']
    rabbitmq_port = 5672
    nova_user = 'nova'
    nova_vhost = '/nova'

    @classmethod
    def setUpState(klass):
        klass.chef_solo({
            'recipes': ['rabbitmq', 'nova::rabbitmq'],
            'rabbitmq': {
                'port': klass.rabbitmq_port
            },
            'nova': {
                'rabbitmq': {
                    'user': klass.nova_user,
                    'vhost': klass.nova_vhost
                }
            }
        })

    def test_nova_user_exists_in_rabbitmq(self):
        cmd = 'rabbitmqctl list_users | grep %s' % (self.nova_user,)
        error_msg = 'There is no user "%s" in RabbitMQ' % (self.nova_user,)
        run_result = self.remote.execute(cmd)
        assert run_result['exit_code'] == 0, error_msg

    def test_nova_vhost_exists_in_rabbitmq(self):
        cmd = 'rabbitmqctl list_vhosts | grep %s' % (self.nova_vhost,)
        error_msg = 'There is no vhost "%s" in RabbitMQ' % (self.nova_vhost,)
        run_result = self.remote.execute(cmd)
        assert run_result['exit_code'] == 0, error_msg
