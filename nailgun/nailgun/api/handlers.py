import os

import simplejson as json
from piston.handler import BaseHandler
from piston.utils import rc
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

from nailgun.models import Environment, Node, Role
from validators import validate_json
from forms import EnvironmentForm, NodeCreationForm, NodeUpdateForm

import celery
from nailgun.tasks import create_chef_config


class TaskHandler(BaseHandler):

    allowed_methods = ('GET',)

    @classmethod
    def render_task(cls, task):
        # TODO show meta?
        repr = {
            "task_id": task.task_id,
            "status": task.state,
        }

        if task.state == celery.states.SUCCESS:
            repr['result'] = task.result
        elif task.state == celery.states.FAILURE:
            # return string representation of the exception if failed
            repr['result'] = str(task.result)

        return repr

    def read(self, request, task_id):
        task = celery.result.AsyncResult(task_id)
        return TaskCollectionHandler.render_task(task)


class ConfigHandler(BaseHandler):

    allowed_methods = ('POST',)

    def create(self, request, environment_id):
        task = create_chef_config.delay(environment_id)

        response = rc.ACCEPTED
        response.content = TaskHandler.render_task(task)
        return response


class EnvironmentCollectionHandler(BaseHandler):

    allowed_methods = ('GET', 'POST')
    model = Environment
    fields = ('id', 'name', ('nodes', ()))

    def read(self, request):
        return Environment.objects.all()

    @validate_json(EnvironmentForm)
    def create(self, request):
        environment = Environment()
        environment.name = request.form.cleaned_data['name']
        environment.save()

        return environment

class EnvironmentHandler(BaseHandler):

    allowed_methods = ('GET',)
    model = Environment
    fields = EnvironmentCollectionHandler.fields

    def read(self, request, environment_id):
        try:
            return Environment.objects.get(pk=environment_id)
        except ObjectDoesNotExist:
            return rc.NOT_FOUND


class NodeCollectionHandler(BaseHandler):

    allowed_methods = ('GET', 'POST')
    model = Node
    fields = ('name', 'environment_id', 'metadata', 'status', ('roles', ()))

    def read(self, request):
        return Node.objects.all()

    @validate_json(NodeCreationForm)
    def create(self, request):
        try:
            node = Node()
            for key, value in request.form.cleaned_data.items():
                if key in request.form.data:
                    setattr(node, key, value)

            node.save()
            return node
        except ObjectDoesNotExist:
            return rc.NOT_FOUND

class NodeHandler(BaseHandler):

    allowed_methods = ('GET', 'PUT')
    model = Node
    fields = NodeCollectionHandler.fields

    def read(self, request, node_name):
        try:
            return Node.objects.get(name=node_name)
        except ObjectDoesNotExist:
            return rc.NOT_FOUND

    @validate_json(NodeUpdateForm)
    def update(self, request, node_name):
        try:
            node = Node.objects.get(name=node_name)
            for key, value in request.form.cleaned_data.items():
                if key in request.form.data:
                    if key == 'environment_id' and value is not None and \
                            node.environment_id is not None:
                        response = rc.BAD_REQUEST
                        response.content = 'Changing environment is not allowed'
                        return response
                    setattr(node, key, value)

            node.save()
            return node
        except ObjectDoesNotExist:
            return rc.NOT_FOUND


class RoleCollectionHandler(BaseHandler):

    allowed_methods = ('GET',)
    model = Role
    fields = ('id', 'name')

    def read(self, request, node_name):
        try:
            return Role.objects.filter(nodes__name=node_name)
        except ObjectDoesNotExist:
            return rc.NOT_FOUND

class RoleHandler(BaseHandler):

    allowed_methods = ('GET', 'POST', 'DELETE')
    model = Role
    fields = RoleCollectionHandler.fields

    def read(self, request, node_name, role_id):
        try:
            return Role.objects.get(nodes__name=node_name, id=role_id)
        except ObjectDoesNotExist:
            return rc.NOT_FOUND

    def create(self, request, node_name, role_id):
        try:
            node = Node.objects.get(name=node_name)
            role = Role.objects.get(id=role_id)

            if role in node.roles.all():
                return rc.DUPLICATE_ENTRY

            node.roles.add(role)

            return role
        except ObjectDoesNotExist:
            return rc.NOT_FOUND

    def delete(self, request, node_name, role_id):
        try:
            node = Node.objects.get(name=node_name)
            role = Role.objects.get(id=role_id)
            node.roles.remove(role)
            return rc.DELETED
        except ObjectDoesNotExist:
            return rc.NOT_FOUND
