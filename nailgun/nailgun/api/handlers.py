import os

import celery
from piston.handler import BaseHandler
from piston.utils import rc
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

from nailgun.models import Environment, Node, Recipe, Role, Release
from nailgun.api.validators import validate_json
from nailgun.api.forms import EnvironmentForm, RecipeForm, RoleForm, \
        NodeCreationForm, NodeUpdateForm, ReleaseCreationForm
#from nailgun.tasks import create_chef_config
from nailgun.tasks import deploy_env


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
        #task = create_chef_config.delay(environment_id)
        task = deploy_env.delay(environment_id)

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
        for key, value in request.form.cleaned_data.items():
            if key in request.form.data:
                setattr(environment, key, value)
        environment.save()

        return environment


class EnvironmentHandler(BaseHandler):

    allowed_methods = ('GET', 'PUT')
    model = Environment
    fields = EnvironmentCollectionHandler.fields

    def read(self, request, environment_id):
        try:
            return Environment.objects.get(id=environment_id)
        except ObjectDoesNotExist:
            return rc.NOT_FOUND

    @validate_json(EnvironmentForm)
    def update(self, request, environment_id):
        try:
            environment = Environment.objects.get(id=environment_id)
            for key, value in request.form.cleaned_data.items():
                if key in request.form.data:
                    setattr(environment, key, value)

            environment.save()
            return environment
        except ObjectDoesNotExist:
            return rc.NOT_FOUND


class NodeCollectionHandler(BaseHandler):

    allowed_methods = ('GET', 'POST')
    model = Node
    fields = ('id', 'name', 'environment_id', 'metadata',
              'status', 'mac', 'fqdn', 'ip', ('roles', ()))

    def read(self, request):
        return Node.objects.all()

    @validate_json(NodeCreationForm)
    def create(self, request):
        node = Node()
        for key, value in request.form.cleaned_data.items():
            if key in request.form.data:
                if key == 'roles':
                    new_roles = Role.objects.filter(id__in=value)
                    node.roles.clear()
                    node.roles.add(*new_roles)
                else:
                    setattr(node, key, value)

        node.save()
        return node


class NodeRoleAvailable(BaseHandler):

    allowed_methods = ('GET',)
    model = Role

    def read(self, request, node_id, role_id):
        # TODO: it's a stub!
        return {'available': True, 'error': None}


class NodeHandler(BaseHandler):

    allowed_methods = ('GET', 'PUT')
    model = Node
    fields = NodeCollectionHandler.fields

    def read(self, request, node_id):
        try:
            return Node.objects.get(id=node_id)
        except ObjectDoesNotExist:
            return rc.NOT_FOUND

    @validate_json(NodeUpdateForm)
    def update(self, request, node_id):
        node, is_created = Node.objects.get_or_create(id=node_id)
        for key, value in request.form.cleaned_data.items():
            if key in request.form.data:
                if key == 'environment_id' and value is not None and \
                        node.environment_id is not None:
                    response = rc.BAD_REQUEST
                    response.content = \
                            'Changing environment is not allowed'
                    return response
                elif key == 'roles':
                    new_roles = Role.objects.filter(id__in=value)
                    node.roles.clear()
                    node.roles.add(*new_roles)
                else:
                    setattr(node, key, value)

        node.save()
        return node


class RecipeCollectionHandler(BaseHandler):

    allowed_methods = ('GET', 'POST')
    model = Recipe
    #fields = ('id', 'name', 'version', ('roles', ()))

    def read(self, request):
        return Recipe.objects.all()

    @validate_json(RecipeForm)
    def create(self, request):
        recipe = Recipe()
        for key, value in request.form.cleaned_data.items():
            if key in request.form.data:
                setattr(recipe, key, value)
        recipe.save()

        return recipe


class RecipeHandler(BaseHandler):

    allowed_methods = ('GET',)
    model = Recipe
    fields = RecipeCollectionHandler.fields

    def read(self, request, recipe_id):
        try:
            return Recipe.objects.get(id=recipe_id)
        except ObjectDoesNotExist:
            return rc.NOT_FOUND


class RoleCollectionHandler(BaseHandler):

    allowed_methods = ('GET', 'POST')
    model = Role
    fields = ('id', 'name')

    def read(self, request):
        return Role.objects.all()

    @validate_json(RoleForm)
    def create(self, request):
        data = request.form.cleaned_data
        recipes = Recipe.objects.filter(recipe__in=data['recipes'])
        role = Role(name=data["name"])
        role.save()
        map(role.recipes.add, recipes)
        role.save()

        return role


class RoleHandler(BaseHandler):

    allowed_methods = ('GET',)
    model = Role
    fields = RoleCollectionHandler.fields

    def read(self, request, role_id):
        try:
            return Role.objects.get(id=role_id)
        except ObjectDoesNotExist:
            return rc.NOT_FOUND


class ReleaseCollectionHandler(BaseHandler):

    allowed_methods = ('GET', 'POST')
    model = Release

    def read(self, request, release_id):
        return Release.objects.all()

    @validate_json(ReleaseCreationForm)
    def create(self, request):
        data = request.form.cleaned_data
        print data
        release = Release(
            name=data["name"],
            version=data["version"],
            description=data["description"]
        )
        release.save()
        role_names = [role["name"] for role in data["roles"]]
        map(release.roles.add, Role.objects.filter(name__in=role_names))
        release.save()
        return release


class ReleaseHandler(BaseHandler):

    allowed_methods = ('GET',)
    model = Release

    def read(self, request, release_id):
        try:
            return Release.objects.get(id=release_id)
        except ObjectDoesNotExist:
            return rc.NOT_FOUND
