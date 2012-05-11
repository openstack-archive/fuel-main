from piston.handler import BaseHandler
from piston.utils import rc
from django.core.exceptions import ObjectDoesNotExist
from ngui.models import Environment, Node

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
    
    allowed_methods = ('GET',)
    model = Node
    fields = ('id', 'name')
    
    def read(self, request, environment_id, node_id=None):
        try:
            if node_id:
                return Node.objects.get(pk=node_id, environment__id=environment_id)
            else:
                return Node.objects.filter(environment__id=environment_id)
        except ObjectDoesNotExist:
            return rc.NOT_FOUND
