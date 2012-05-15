import logging


class ProvisionerException:
    def __init__(self, message=""):
        self.message = message

    def __str__(self):
        return self.message


class Provisioner:
    """
    Abstract provisioner. 

    FIXME: 
    At the moment you have to use child classes like ProvisionerCobbler that implement 
    abstract provisioner api. For future it would be nice to use Provisioner itself and 
    initialize definite implementation via config data.
    """

    logger_name = 'provisioner'

    def set_node(self, **data):
        raise ProvisionerException("Must be implemented")

    def list_nodes(self):
        raise ProvisionerException("Must be implemented")







