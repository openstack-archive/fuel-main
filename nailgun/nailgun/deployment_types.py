import itertools

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
        roles = cluster.release.roles.all()
        nodes = itertools.cycle(cluster.nodes.all())
        new_roles = {}
        for role in roles:
            node = nodes.next()
            node.new_roles.add(role)
            node.redeployment_needed = True
            node.save()
