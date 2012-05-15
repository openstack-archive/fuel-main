import simplejson as json

from piston.handler import BaseHandler
from piston.utils import rc
from django.core.exceptions import ObjectDoesNotExist
from nailgun.models import Environment, Node


class EnvironmentHandler(BaseHandler):
    
    allowed_methods = ('GET',)
    model = Environment
    fields = ('id', 'name', ('nodes', ()))
    
    def read(self, request, environment_id=None):
        if environment_id:
            try:
                return Environment.objects.get(pk=environment_id)
            except ObjectDoesNotExist:
                return rc.NOT_FOUND
        else:
            return Environment.objects.all()


class NodeHandler(BaseHandler):
    
    allowed_methods = ('GET', 'PUT',)
    model = Node
    fields = ('name', 'metadata')
    
    def read(self, request, environment_id, name=None):
        try:
            if name:
                return Node.objects.get(name=name, environment__id=environment_id)
            else:
                return Node.objects.filter(environment__id=environment_id)
        except ObjectDoesNotExist:
            return rc.NOT_FOUND

    def update(self, request, environment_id, name):
        if request.content_type != "application/json":
            return rc.BAD_REQUEST

        data = json.loads(request.body)
        if not 'block_device' in data:
            return rc.BAD_REQUEST
        if not 'interfaces' in data:
            return rc.BAD_REQUEST
        if not 'cpu' in data:
            return rc.BAD_REQUEST
        if not 'memory' in data:
            return rc.BAD_REQUEST

        node = Node(name=name,
                    environment_id=environment_id,
                    metadata=data)
        node.save()
