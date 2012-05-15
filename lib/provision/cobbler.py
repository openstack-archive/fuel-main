import logging
import xmlrpclib

from . import Provisioner, ProvisionerException

class CobblerProvisioner(Provisioner):
    """
    Cobbler provisioner.
    """

    def __init__(self, cobbler_url, cobbler_user, cobbler_password):
        self.logger = logging.getLogger(self.logger_name)

        self.cobbler_url = cobbler_url
        self.cobbler_user = cobbler_user
        self.cobbler_password = cobbler_password

        self.logger.debug('Cobbler config: url="%s", user="%s", password="%s"' % (cobbler_url, cobbler_user, cobbler_password))

        self.server = xmlrpclib.Server(self.cobbler_url)
        try:
            self.token = self.server.login(self.cobbler_user, self.cobbler_password)
        except Exception as e:
            self.logger.error('Error occured while connecting to cobbler server.')
            raise e


    def set_node(self, **data):
        pass


    def list_nodes(self):
        return self.server.get_systems()

