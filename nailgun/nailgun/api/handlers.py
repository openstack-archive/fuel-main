import os

import celery
from piston.handler import BaseHandler
from piston.utils import rc
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

from nailgun.models import Cluster, Node, Cookbook, Role, Release
from nailgun.api.validators import validate_json
from nailgun.api.forms import ClusterForm, CookbookForm, RoleForm, \
        NodeCreationForm, NodeUpdateForm, ReleaseCreationForm
#from nailgun.tasks import create_chef_config
from nailgun.tasks import deploy_cluster


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

    def create(self, request, cluster_id):
        #task = create_chef_config.delay(cluster_id)
        task = deploy_cluster.delay(cluster_id)

        response = rc.ACCEPTED
        response.content = TaskHandler.render_task(task)
        return response


class ClusterCollectionHandler(BaseHandler):

    allowed_methods = ('GET', 'POST')
    model = Cluster
    fields = ('id', 'name', ('nodes', ()))

    def read(self, request):
        return Cluster.objects.all()

    @validate_json(ClusterForm)
    def create(self, request):
        cluster = Cluster()
        for key, value in request.form.cleaned_data.items():
            if key in request.form.data:
                setattr(cluster, key, value)
        cluster.save()

        return cluster


class ClusterHandler(BaseHandler):

    allowed_methods = ('GET', 'PUT')
    model = Cluster
    fields = ClusterCollectionHandler.fields

    def read(self, request, cluster_id):
        try:
            return Cluster.objects.get(id=cluster_id)
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
            return cluster
        except ObjectDoesNotExist:
            return rc.NOT_FOUND


class NodeCollectionHandler(BaseHandler):

    allowed_methods = ('GET', 'POST')
    model = Node
    fields = ('id', 'name', 'cluster_id', 'metadata',
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
        return node


class CookbookCollectionHandler(BaseHandler):

    allowed_methods = ('GET', 'POST')
    model = Cookbook
    fields = ('id', 'name', 'version', ('roles', ()))

    def read(self, request):
        return Cookbook.objects.all()

    @validate_json(CookbookForm)
    def create(self, request):
        cookbook = Cookbook()
        for key, value in request.form.cleaned_data.items():
            if key in request.form.data:
                setattr(cookbook, key, value)
        cookbook.save()

        return cookbook


class CookbookHandler(BaseHandler):

    allowed_methods = ('GET',)
    model = Cookbook
    fields = CookbookCollectionHandler.fields

    def read(self, request, cookbook_id):
        try:
            return Cookbook.objects.get(id=cookbook_id)
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
        role = Role()
        for key, value in request.form.cleaned_data.items():
            if key in request.form.data:
                setattr(role, key, value)
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
