deployment_types = {}


class TypeRegistrator(type):
    def __init__(cls, name, bases, dct):
        super(TypeRegistrator, cls).__init__(name, bases, dct)
        if hasattr(cls, 'id'):
            deployment_types[cls.id] = cls


class BaseDeploymentType(object):
    __metaclass__ = TypeRegistrator


class SimpleDeploymentType(BaseDeploymentType):
    id = 'simple'
    name = 'Simple Deployment'
    description = 'Simple OpenStack deployment'

    @classmethod
    def assign_roles(cls, cluster):
        # TODO: replace logic
        for node in cluster.nodes.all():
            node.new_roles.clear()
            node.redeployment_needed = True
            node.save()
