import os

import simplejson as json
from piston.handler import BaseHandler
from piston.utils import rc
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

from nailgun.models import Environment, Node, Role
from validators import validate_json
from forms import EnvironmentForm, NodeForm


class EnvironmentHandler(BaseHandler):

    allowed_methods = ('GET', 'POST', 'PUT')
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
        return environment


class ConfigHandler(BaseHandler):

    allowed_methods = ('POST',)

    """ Creates JSON files for chef-solo. This should be moved to the queue """
    def create(self, request, environment_id):
        env_id = environment_id
        nodes = Node.objects.filter(environment__id=env_id)
        roles = Role.objects.all()
        if not (nodes and roles):
            resp = rc.NOT_FOUND
            resp.write("Roles or Nodes list is empty")
            return resp

        nodes_per_role = {}
        # For each role in the system
        for r in roles:
            # Find nodes that have this role. Filter nodes by env_id
            nodes_per_role[r.name] = \
                    [x.name for x in r.nodes.filter(environment__id=env_id)]

        solo_json = {}
        # Extend solo_json for each node by specifying role
        #    assignment for this particular node
        for n in nodes:
            solo_json['run_list'] = \
                    ["role[" + x.name + "]" for x in n.roles.all()]
            solo_json['all_roles'] = nodes_per_role

            filepath = os.path.join(settings.CHEF_CONF_FOLDER,
                    n.name + '.json')
            f = open(filepath, 'w')
            f.write(json.dumps(solo_json))
            f.close()


class NodeHandler(BaseHandler):

    allowed_methods = ('GET', 'PUT')
    model = Node
    fields = ('name', 'metadata', 'status', ('roles', ()))

    def read(self, request, environment_id, node_name=None):
        try:
            if node_name:
                return Node.objects.get(name=node_name,
                        environment__id=environment_id)
            else:
                return Node.objects.filter(environment__id=environment_id)
        except ObjectDoesNotExist:
            return rc.NOT_FOUND

    @validate_json(NodeForm)
    def update(self, request, environment_id, node_name):
        try:
            node = Node.objects.get(name=node_name,
                    environment__id=environment_id)
            for key, value in request.form.cleaned_data.items():
                # check if parameter is really passed by client
                if key in request.form.data:
                    setattr(node, key, value)
            node.save()
            return node
        except ObjectDoesNotExist:
            return rc.NOT_FOUND


class RoleHandler(BaseHandler):

    allowed_methods = ('GET', 'POST', 'DELETE')
    model = Role
    fields = ('id', 'name')

    def read(self, request, environment_id, node_name, role_id=None):
        try:
            if role_id:
                return Role.objects.get(nodes__environment__id=environment_id,
                        nodes__name=node_name, id=role_id)
            else:
                return Role.objects.filter(
                        nodes__environment__id=environment_id,
                        nodes__name=node_name)
        except ObjectDoesNotExist:
            return rc.NOT_FOUND

    def create(self, request, environment_id, node_name, role_id):
        try:
            node = Node.objects.get(environment__id=environment_id,
                    name=node_name)
            role = Role.objects.get(id=role_id)

            if role in node.roles.all():
                return rc.DUPLICATE_ENTRY

            node.roles.add(role)
            return role
        except ObjectDoesNotExist:
            return rc.NOT_FOUND

    def delete(self, request, environment_id, node_name, role_id):
        try:
            node = Node.objects.get(environment__id=environment_id,
                    name=node_name)
            role = Role.objects.get(id=role_id)
            node.roles.remove(role)
            return rc.DELETED
        except ObjectDoesNotExist:
            return rc.NOT_FOUND
