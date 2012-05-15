import logging
import xmlrpclib
from provisioner import ProvisionerException
from provisioner import Provisioner



class ProvisionerCobbler(Provisioner):
    """
    Cobbler provisioner implementation.
    """

    def __init__(self, **data):
        self.logger = logging.getLogger(self.logger_name)


        if 'cobbler_url' not in data:
            self.logger.error('Cobbler url was not provided.')
            raise ProvisionerException("You must provide cobbler_url.")

        self.logger.debug('Cobbler url provided: %s' % str(data['cobbler_url']))
        self.cobbler_url = data['cobbler_url']

        if 'cobbler_user' not in data or 'cobbler_password' not in data:
            self.logger.error('Cobbler credentials were not provided correctly.')
            raise ProvisionerException("You must provide cobbler_user and cobbler_password.")
            
        self.logger.debug('Cobbler credentials: cobbler_user=%s, cobbler_password=%s' % (str(data['cobbler_user']), str(data['cobbler_password'])))

        self.cobbler_user = data['cobbler_user']
        self.cobbler_password = data['cobbler_password']

        try:
            self.server = xmlrpclib.Server(self.cobbler_url)
            self.token = self.server.login(self.cobbler_user, self.cobbler_password)
        except Exception as e:
            self.logger.error('Error occured while connecting to cobbler server.')
            raise e


    def set_node(self, **data):
        pass


    def list_nodes(self):
        return self.server.get_systems()
