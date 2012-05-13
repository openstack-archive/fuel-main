import simplejson as json

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

    def update(self, request, environment_id, name=None):
        # TODO: use another exception. Check if request contains valid data
        # It also fales if there is no name
        try:
            data = json.loads(request.raw_post_data)
            node = Node(name=name,
                        environment_id=environment_id,
                        metadata=data)
            node.save()
        except ObjectDoesNotExist:
            return rc.NOT_FOUND
