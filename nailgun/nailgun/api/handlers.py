import os

import simplejson as json
from piston.handler import BaseHandler
from piston.utils import rc
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

from nailgun.models import Environment, Node, Role
from validators import validate_json
from forms import EnvironmentForm, NodeForm

from nailgun.tasks import create_chef_config


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

    def create(self, request, environment_id):
        create_chef_config.delay(environment_id)
        return rc.ACCEPTED


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
