import simplejson as json

from piston.handler import BaseHandler
from piston.utils import rc
from django.core.exceptions import ObjectDoesNotExist
from nailgun.models import Environment, Node, Role
from validators import validate_json
from forms import EnvironmentForm


class EnvironmentHandler(BaseHandler):
    
    allowed_methods = ('GET', 'POST')
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
    
    @validate_json(EnvironmentForm)
    def create(self, request):
        environment = Environment()
        environment.name = request.form.cleaned_data['name']
        environment.save()
        return rc.CREATED


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


class RoleHandler(BaseHandler):

    model = Role

    def read(self, request, environment_id, name):
        node = Node.objects.filter(environment_id=environment_id,
                name=name)[0]
        return node.roles.all()

    def update(self, request, environment_id, name):
        if request.content_type != "application/json":
            return rc.BAD_REQUEST

        try:
            node = Node.objects.get(name=name, environment__id=environment_id)
        except ObjectDoesNotExist:
            return rc.NOT_FOUND


        roles = json.loads(request.body)
        # TODO: use filter to check if all passed have 'name' attr. If not - return BAD REQUEST
        try:
            [r['name'] for r in roles]
        except:
            return rc.BAD_REQUEST

        #node.roles = []
        for r in roles:
            if not 'name' in r:
                return rc.BAD_REQUEST
            # What if it exists already?
            # need to make it uniq or name for role should be pk
            # Another thing is it would be better to do role saving transactionally,
            #   i.e. save all or none in case of any error, as well as node update
            role_in_db = Role(name=r['name'])
            role_in_db.save()

            node.roles.add(role_in_db)

        # It looks like we don't need to save now - do we?
        node.save()
