import os

import celery
from piston.handler import BaseHandler
from piston.utils import rc
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

from nailgun.models import Cluster, Node, Recipe, Role, Release
from nailgun.api.validators import validate_json
from nailgun.api.forms import ClusterForm, RecipeForm, RoleForm, \
        NodeCreationForm, NodeUpdateForm, ReleaseCreationForm
#from nailgun.tasks import create_chef_config
from nailgun.tasks import deploy_cluster


class JSONHandler(BaseHandler):
    """
    Basic JSON handler
    """
    fields = None
    special_fields = None

    @classmethod
    def render(cls, item, fields=None):
        json_data = {}
        use_fields = fields if fields else cls.fields
        if not use_fields:
            raise ValueError("No fields for serialize")
        for field in use_fields:
            if cls is JSONHandler or cls.special_fields and \
                field not in cls.special_fields:
                json_data[field] = getattr(item, field)
        return json_data


class TaskHandler(BaseHandler):

    allowed_methods = ('GET',)
    fields = ('task_id', 'status')
    special_fields = ('result',)

    @classmethod
    def render(cls, task):
        # TODO show meta?
        json_data = {
            "task_id": task.task_id,
            "status": task.state,
        }

        if task.state == celery.states.SUCCESS:
            json_data['result'] = task.result
        elif task.state == celery.states.FAILURE:
            # return string representation of the exception if failed
            json_data['result'] = str(task.result)

        return json_data

    def read(self, request, task_id):
        try:
            task = celery.result.AsyncResult(task_id)
        except:
            return rc.NOT_FOUND
        return TaskHandler.render(task)


class ConfigHandler(BaseHandler):

    allowed_methods = ('POST',)

    def create(self, request, cluster_id):
        #task = create_chef_config.delay(cluster_id)
        task = deploy_cluster.delay(cluster_id)

        response = rc.ACCEPTED
        response.content = TaskHandler.render(task)
        return response


class ClusterCollectionHandler(BaseHandler):

    allowed_methods = ('GET', 'POST')
    model = Cluster

    def read(self, request):
        json_data = map(
            ClusterHandler.render,
            Cluster.objects.all()
        )
        return json_data

    @validate_json(ClusterForm)
    def create(self, request):
        cluster = Cluster()
        for key, value in request.form.cleaned_data.items():
            if key in request.form.data:
                setattr(cluster, key, value)
        cluster.save()

        return ClusterHandler.render(cluster)


class ClusterHandler(JSONHandler):

    allowed_methods = ('GET', 'PUT')
    model = Cluster
    fields = ('id', 'name')
    special_fields = ('nodes',)

    @classmethod
    def render(cls, cluster, fields=None):
        json_data = JSONHandler.render(cluster, fields=fields or cls.fields)
        for field in cls.special_fields:
            if field in ('nodes',):
                json_data[field] = map(
                    NodeHandler.render,
                    cluster.nodes.all()
                )
        return json_data

    def read(self, request, cluster_id):
        try:
            cluster = Cluster.objects.get(id=cluster_id)
            return ClusterHandler.render(cluster)
        except ObjectDoesNotExist:
            return rc.NOT_FOUND

    @validate_json(ClusterForm)
    def update(self, request, cluster_id):
        try:
            cluster = Cluster.objects.get(id=cluster_id)
            for key, value in request.form.cleaned_data.items():
                if key in request.form.data:
                    setattr(cluster, key, value)

            cluster.save()
            return ClusterHandler.render(cluster)
        except ObjectDoesNotExist:
            return rc.NOT_FOUND


class NodeCollectionHandler(BaseHandler):

    allowed_methods = ('GET', 'POST')
    model = Node

    def read(self, request):
        return map(
            NodeHandler.render,
            Node.objects.all()
        )

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
        return NodeHandler.render(node)


class NodeHandler(JSONHandler):

    allowed_methods = ('GET', 'PUT')
    model = Node
    fields = ('id', 'name', 'cluster_id', 'metadata',
            'status', 'mac', 'fqdn', 'ip')
    special_fields = ('roles',)

    @classmethod
    def render(cls, node, fields=None):
        json_data = JSONHandler.render(node, fields=fields or cls.fields)
        for field in cls.special_fields:
            if field in ('roles',):
                json_data[field] = map(
                    RoleHandler.render,
                    node.roles.all()
                )
        return json_data

    def read(self, request, node_id):
        try:
            node = Node.objects.get(id=node_id)
            return NodeHandler.render(node)
        except ObjectDoesNotExist:
            return rc.NOT_FOUND

    @validate_json(NodeUpdateForm)
    def update(self, request, node_id):
        node, is_created = Node.objects.get_or_create(id=node_id)
        for key, value in request.form.cleaned_data.items():
            if key in request.form.data:
                if key == 'cluster_id' and value is not None and \
                        node.cluster_id is not None:
                    response = rc.BAD_REQUEST
                    response.content = \
                            'Changing cluster is not allowed'
                    return response
                elif key == 'roles':
                    new_roles = Role.objects.filter(id__in=value)
                    node.roles.clear()
                    node.roles.add(*new_roles)
                else:
                    setattr(node, key, value)

        node.save()
        return NodeHandler.render(node)


class NodeRoleAvailable(BaseHandler):

    allowed_methods = ('GET',)
    model = Role

    def read(self, request, node_id, role_id):
        # TODO: it's a stub!
        return {'available': True, 'error': None}


class RecipeCollectionHandler(BaseHandler):

    allowed_methods = ('GET', 'POST')
    model = Recipe

    def read(self, request):
        return map(
            RecipeHandler.render,
            Recipe.objects.all()
        )

    @validate_json(RecipeForm)
    def create(self, request):
        data = request.form.cleaned_data
        try:
            release = Recipe.objects.get(
                recipe=data['recipe']
            )
            return rc.DUPLICATE_ENTRY
        except Recipe.DoesNotExist:
            pass

        recipe = Recipe()
        for key, value in data.items():
            if key in request.form.data:
                setattr(recipe, key, value)
        recipe.save()

        return RecipeHandler.render(recipe)


class RecipeHandler(JSONHandler):

    allowed_methods = ('GET',)
    model = Recipe
    special_fields = ('recipe',)

    @classmethod
    def render(cls, recipe, fields=None):
        return getattr(recipe, 'recipe')

    def read(self, request, recipe_id):
        try:
            recipe = Recipe.objects.get(id=recipe_id)
            return RecipeHandler.render(recipe)
        except ObjectDoesNotExist:
            return rc.NOT_FOUND


class RoleCollectionHandler(BaseHandler):

    allowed_methods = ('GET', 'POST')
    model = Role

    def read(self, request):
        return map(
            RoleHandler.render,
            Role.objects.all()
        )

    @validate_json(RoleForm)
    def create(self, request):
        data = request.form.cleaned_data
        recipes = Recipe.objects.filter(recipe__in=data['recipes'])
        role = Role(name=data["name"])
        role.save()
        map(role.recipes.add, recipes)
        role.save()

        return RoleHandler.render(role)


class RoleHandler(JSONHandler):

    allowed_methods = ('GET',)
    model = Role
    fields = ('id', 'name')
    special_fields = ('recipes',)

    @classmethod
    def render(cls, role, fields=None):
        json_data = JSONHandler.render(role, fields=fields or cls.fields)
        for field in cls.special_fields:
            if field in ('recipes',):
                json_data[field] = map(
                    RecipeHandler.render,
                    role.recipes.all()
                )
        return json_data

    def read(self, request, role_id):
        try:
            role = Role.objects.get(id=role_id)
            RoleHandler.render(role)
        except ObjectDoesNotExist:
            return rc.NOT_FOUND


class ReleaseCollectionHandler(BaseHandler):

    allowed_methods = ('GET', 'POST')
    model = Release

    def read(self, request):
        return map(
            ReleaseHandler.render,
            Release.objects.all()
        )

    @validate_json(ReleaseCreationForm)
    def create(self, request):
        data = request.form.cleaned_data

        try:
            release = Release.objects.get(
                name=data['name'],
                version=data['version']
            )
            return rc.DUPLICATE_ENTRY
        except Release.DoesNotExist:
            pass

        release = Release(
            name=data["name"],
            version=data["version"],
            description=data["description"]
        )
        release.save()

        for role in data["roles"]:
            rl = Role(name=role["name"])
            rl.save()
            recipes = Recipe.objects.filter(recipe__in=role["recipes"])
            map(rl.recipes.add, recipes)
            rl.save()
            release.roles.add(rl)

        release.save()
        return ReleaseHandler.render(release)


class ReleaseHandler(JSONHandler):

    allowed_methods = ('GET',)
    model = Release
    fields = ('name', 'version', 'description')
    special_fields = ('roles',)

    @classmethod
    def render(cls, release, fields=None):
        json_data = JSONHandler.render(release, fields=fields or cls.fields)
        for field in cls.special_fields:
            if field in ('roles',):
                json_data[field] = map(
                    RoleHandler.render,
                    release.roles.all()
                )
        return json_data

    def read(self, request, release_id):
        try:
            release = Release.objects.get(id=release_id)
            return ReleaseHandler.render(release)
        except ObjectDoesNotExist:
            return rc.NOT_FOUND
