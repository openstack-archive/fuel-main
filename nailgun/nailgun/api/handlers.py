import os

import celery
from piston.handler import BaseHandler
from piston.utils import rc, validate
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

from nailgun.models import Cluster, Node, Recipe, Role, Release
from nailgun.api.validators import validate_json
from nailgun.api.forms import ClusterForm, ClusterCreationForm, RecipeForm, \
        RoleForm, RoleFilterForm, NodeCreationForm, NodeFilterForm, NodeForm, \
        ReleaseCreationForm
from nailgun import tasks


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
        json_data = {
            "task_id": task.task_id,
            "status": task.state,
            "subtasks": None,
            "result": None,
            "error": None,
            "traceback": None,
        }

        if isinstance(task.result, celery.result.ResultSet):
            json_data['subtasks'] = [TaskHandler.render(t) for t in \
                    task.result.results]
        elif isinstance(task.result, celery.result.AsyncResult):
            json_data['subtasks'] = [TaskHandler.render(task.result)]
        elif isinstance(task.result, Exception):
            json_data['error'] = task.result
            json_data['traceback'] = task.traceback
        else:
            json_data['result'] = task.result

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
        try:
            cluster = Cluster.objects.get(id=cluster_id)
        except ObjectDoesNotExist:
            return rc.NOT_FOUND

        task = tasks.deploy_cluster.delay(cluster_id)

        # FIXME: move to task?
        for node in cluster.nodes.all():
            node.new_roles.clear()
            node.redeployment_needed = False
            node.save()

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

    @validate_json(ClusterCreationForm)
    def create(self, request):
        cluster = Cluster()
        for key, value in request.form.cleaned_data.items():
            if key in request.form.data:
                if key != 'nodes':
                    setattr(cluster, key, value)

        cluster.save()

        if 'nodes' in request.form.data:
            nodes = Node.objects.filter(
                id__in=request.form.cleaned_data['nodes']
            )
            cluster.nodes.add(*nodes)

        return ClusterHandler.render(cluster)


class ClusterHandler(JSONHandler):

    allowed_methods = ('GET', 'PUT')
    model = Cluster
    fields = ('id', 'name')
    special_fields = ('nodes', 'release')

    @classmethod
    def render(cls, cluster, fields=None):
        json_data = JSONHandler.render(cluster, fields=fields or cls.fields)
        for field in cls.special_fields:
            if field in ('nodes',):
                json_data[field] = map(
                    NodeHandler.render,
                    cluster.nodes.all()
                )
            elif field in ('release',):
                json_data[field] = ReleaseHandler.render(cluster.release)

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
                    if key == 'nodes':
                        new_nodes = Node.objects.filter(id__in=value)
                        cluster.nodes.clear()
                        cluster.nodes.add(*new_nodes)
                    else:
                        setattr(cluster, key, value)

            cluster.save()
            return ClusterHandler.render(cluster)
        except ObjectDoesNotExist:
            return rc.NOT_FOUND


class NodeCollectionHandler(BaseHandler):

    allowed_methods = ('GET', 'POST')
    model = Node

    @validate(NodeFilterForm, 'GET')
    def read(self, request):
        nodes = Node.objects.all()
        if 'cluster_id' in request.form.data:
            nodes = nodes.filter(
                cluster_id=request.form.cleaned_data['cluster_id'])
        return map(NodeHandler.render, nodes)

    @validate_json(NodeCreationForm)
    def create(self, request):
        node = Node()
        for key, value in request.form.cleaned_data.items():
            if key in request.form.data:
                if key != 'new_roles':
                    setattr(node, key, value)

        node.save()
        return NodeHandler.render(node)


class NodeHandler(JSONHandler):

    allowed_methods = ('GET', 'PUT')
    model = Node
    fields = ('id', 'name', 'metadata', 'status', 'mac', 'fqdn', 'ip',
              'redeployment_needed')
    special_fields = ('roles', 'new_roles')

    @classmethod
    def render(cls, node, fields=None):
        json_data = JSONHandler.render(node, fields=fields or cls.fields)
        for field in cls.special_fields:
            if field in ('roles', 'new_roles'):
                json_data[field] = map(
                    RoleHandler.render,
                    getattr(node, field).all()
                )
        return json_data

    def read(self, request, node_id):
        try:
            node = Node.objects.get(id=node_id)
            return NodeHandler.render(node)
        except ObjectDoesNotExist:
            return rc.NOT_FOUND

    @validate_json(NodeForm)
    def update(self, request, node_id):
        node, is_created = Node.objects.get_or_create(id=node_id)
        for key, value in request.form.cleaned_data.items():
            if key in request.form.data:
                if key == 'new_roles':
                    new_roles = Role.objects.filter(id__in=value)
                    node.new_roles.clear()
                    node.new_roles.add(*new_roles)
                else:
                    setattr(node, key, value)

        node.save()
        return NodeHandler.render(node)


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

    @validate(RoleFilterForm, 'GET')
    def read(self, request):
        roles = Role.objects.all()
        if 'node_id' in request.form.data:
            result = []
            for role in roles:
                # TODO role filtering
                # use request.form.cleaned_data['node_id'] to filter roles
                if False:
                    continue
                # if the role is suitable for the node, set 'available' field
                # to True. If it is not, set it to False and also describe the
                # reason in 'reason' field of rendered_role
                rendered_role = RoleHandler.render(role)
                rendered_role['available'] = True
                result.append(rendered_role)
            return result
        else:
            return map(RoleHandler.render, roles)

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
    fields = ('id', 'name', 'version', 'description')
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
