import os

import celery
import ipaddr
import json
from piston.handler import BaseHandler
from piston.utils import rc, validate
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

from nailgun.models import Cluster, Node, Recipe, Role, Release, Network, \
        Attribute, Task
from nailgun.deployment_types import deployment_types
from nailgun.api.validators import validate_json, validate_json_list
from nailgun.api.forms import ClusterForm, ClusterCreationForm, RecipeForm, \
        RoleForm, RoleFilterForm, NodeCreationForm, NodeFilterForm, NodeForm, \
        ReleaseCreationForm, NetworkCreationForm, AttributeForm
from nailgun import tasks
import nailgun.api.validators as vld


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

    @classmethod
    def render(cls, task):
        def render_task_result(task_result):
            # TODO: eliminate subtasks and simplify output
            json_data = {
                "task_id": task_result.task_id,
                "status": task_result.state,
                "ready": task_result.ready(),
                "subtasks": None,
                "result": None,
                "error": None,
                "traceback": None,
            }

            if isinstance(task_result.result, celery.result.ResultSet):
                json_data['subtasks'] = [render_task_result(t) for t in \
                        task_result.result.results]
            elif isinstance(task_result.result, celery.result.AsyncResult):
                json_data['subtasks'] = \
                        [render_task_result(task_result.result)]
            elif isinstance(task_result.result, Exception):
                json_data['error'] = task_result.result
                json_data['traceback'] = task_result.traceback
            else:
                json_data['result'] = task_result.result

            return json_data

        json_data = render_task_result(task.result)
        json_data['name'] = task.name

        return json_data

    def read(self, request, task_id):
        try:
            task = Task.objects.get(id=task_id)
        except ObjectDoesNotExist:
            return rc.NOT_FOUND

        return TaskHandler.render(task)


class ClusterChangesHandler(BaseHandler):

    allowed_methods = ('PUT', 'DELETE')

    def update(self, request, cluster_id):
        try:
            cluster = Cluster.objects.get(id=cluster_id)
        except ObjectDoesNotExist:
            return rc.NOT_FOUND

        if cluster.task:
            if cluster.task.ready:
                cluster.task.delete()
            else:
                response = rc.DUPLICATE_ENTRY
                response.content = "Another task is running"
                return response

        for node in cluster.nodes.filter(redeployment_needed=True):
            node.roles = node.new_roles.all()
            node.new_roles.clear()
            node.redeployment_needed = False
            node.save()

        for nw in cluster.release.networks.all():
            for node in cluster.nodes.all():
                nw.update_node_network_info(node)

        task = Task(task_name='deploy_cluster', cluster=cluster)
        task.run(cluster_id)

        response = rc.ACCEPTED
        response.content = TaskHandler.render(task)
        return response

    def delete(self, request, cluster_id):
        try:
            cluster = Cluster.objects.get(id=cluster_id)
        except ObjectDoesNotExist:
            return rc.NOT_FOUND

        for node in cluster.nodes.filter(redeployment_needed=True):
            node.new_roles.clear()
            node.redeployment_needed = False
            node.save()

        return rc.DELETED


class DeploymentTypeCollectionHandler(JSONHandler):

    allowed_methods = ('GET',)

    def read(self, request, cluster_id):
        try:
            cluster = Cluster.objects.get(id=cluster_id)
        except ObjectDoesNotExist:
            return rc.NOT_FOUND

        return map(DeploymentTypeHandler.render, deployment_types.values())


class DeploymentTypeHandler(JSONHandler):

    allowed_methods = ('PUT',)
    fields = ('id', 'name', 'description')

    @classmethod
    def render(cls, deployment_type, fields=None):
        return JSONHandler.render(deployment_type, fields=fields or cls.fields)

    def update(self, request, cluster_id, deployment_type_id):
        try:
            cluster = Cluster.objects.get(id=cluster_id)
            deployment_type = deployment_types[deployment_type_id]
        except ObjectDoesNotExist:
            return rc.NOT_FOUND

        deployment_type.assign_roles(cluster)

        return {}


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

        # TODO: solve vlan issues
        vlan_ids = {
            'storage': 200,
            'public': 300,
            'floating': 300,
            'fixed': 500,
            'management': 100
        }

        for network in cluster.release.networks_metadata:
            access = network['access']
            if access not in settings.NETWORK_POOLS:
                raise Exception("Incorrect access mode for network")

            for nw_pool in settings.NETWORK_POOLS[access]:
                nw_ip = ipaddr.IPv4Network(nw_pool)
                new_network = None
                for net in nw_ip.iter_subnets(new_prefix=24):
                    try:
                        nw_exist = Network.objects.get(network=net)
                    except Network.DoesNotExist:
                        new_network = net
                        break

                if new_network:
                    break

            nw = Network(
                release=cluster.release,
                name=network['name'],
                access=access,
                network=str(new_network),
                gateway=str(new_network[1]),
                range_l=str(new_network[2]),
                range_h=str(new_network[-1]),
                vlan_id=vlan_ids[network['name']]
            )
            nw.save()

        if 'nodes' in request.form.data:
            nodes = Node.objects.filter(
                id__in=request.form.cleaned_data['nodes']
            )
            cluster.nodes = nodes

        return ClusterHandler.render(cluster)


class ClusterHandler(JSONHandler):

    allowed_methods = ('GET', 'PUT', 'DELETE')
    model = Cluster
    fields = ('id', 'name')
    special_fields = ('nodes', 'release', 'task')

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
            elif field in ('task',):
                json_data[field] = cluster.task and \
                                   TaskHandler.render(cluster.task) or None

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
                        cluster.nodes = new_nodes
                    elif key == 'task':
                        cluster.task.delete()
                    else:
                        setattr(cluster, key, value)

            cluster.save()
            return ClusterHandler.render(cluster)
        except ObjectDoesNotExist:
            return rc.NOT_FOUND

    def delete(self, request, cluster_id):
        try:
            cluster = Cluster.objects.get(id=cluster_id)
            cluster.delete()
            return rc.DELETED
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

    allowed_methods = ('GET', 'PUT', 'DELETE')
    model = Node
    fields = ('id', 'name', 'metadata', 'status', 'mac', 'fqdn', 'ip',
              'manufacturer', 'platform_name', 'redeployment_needed')
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
                    node.new_roles = new_roles
                else:
                    setattr(node, key, value)

        node.save()
        return NodeHandler.render(node)

    def delete(self, request, node_id):
        try:
            node = Node.objects.get(id=node_id)
            node.delete()
            return rc.DELETED
        except ObjectDoesNotExist:
            return rc.NOT_FOUND


class AttributeCollectionHandler(BaseHandler):

    allowed_methods = ('GET', 'PUT')
    model = Attribute

    fields = ('id', 'cookbook', 'version', 'attribute')

    @validate_json(AttributeForm)
    def update(self, request):
        data = request.form.cleaned_data
        attr, is_created = Attribute.objects.get_or_create(
                cookbook=data['cookbook'],
                version=data['version']
        )
        attr.attribute = data['attribute']
        attr.save()
        return attr.id


class AttributeHandler(BaseHandler):

    allowed_methods = ('GET',)
    model = Attribute

    fields = ('id', 'cookbook', 'version', 'attribute')

    def read(self, request, attribute_id):
        try:
            return Attribute.objects.get(id=attribute_id)
        except ObjectDoesNotExist:
            return rc.NOT_FOUND


class RecipeCollectionHandler(BaseHandler):

    allowed_methods = ('GET', 'POST', 'PUT')
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

        recipe = Recipe(recipe=data['recipe'])
        recipe.save()
        for key, value in data.items():
            if key == 'depends':
                for dep in value:
                    try:
                        d = Recipe.objects.get(recipe=dep)
                    except Recipe.DoesNotExist:
                        d = Recipe(recipe=dep)
                        d.save()
            else:
                setattr(recipe, key, value)
        recipe.save()

        return RecipeHandler.render(recipe)

    @validate_json_list(RecipeForm)
    def update(self, request):
        for form in request.forms:
            attr = form.cleaned_data["attribute"]
            create_depends = []
            for depend in form.cleaned_data["depends"]:
                try:
                    d = Recipe.objects.get(recipe=depend)
                except Recipe.DoesNotExist:
                    d = Recipe(recipe=depend)
                    d.save()
                create_depends.append(d)
            try:
                r = Recipe.objects.get(recipe=form.cleaned_data["recipe"])
            except Recipe.DoesNotExist:
                r = Recipe(recipe=form.cleaned_data["recipe"])
                r.save()
            r.depends = create_depends
            if attr:
                r.attribute = attr
            r.save()
        return rc.CREATED


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
            description=data["description"],
            networks_metadata=data["networks_metadata"]
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

    allowed_methods = ('GET', 'DELETE')
    model = Release
    fields = ('id', 'name', 'version', 'description', 'networks_metadata')
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

    def delete(self, request, release_id):
        try:
            release = Release.objects.get(id=release_id)
            release.delete()
            return rc.DELETED
        except ObjectDoesNotExist:
            return rc.NOT_FOUND


class NetworkHandler(JSONHandler):

    allowed_methods = ('GET',)
    model = Network
    fields = ('id', 'network', 'name', 'access',
            'vlan_id', 'range_l', 'range_h', 'gateway')
    special_fields = ('release', 'nodes')

    @classmethod
    def render(cls, network, fields=None):
        json_data = JSONHandler.render(network, fields=fields or cls.fields)
        for field in cls.special_fields:
            if field == 'release':
                json_data['release_id'] = network.release_id
            elif field == 'nodes':
                json_data[field] = map(
                    NodeHandler.render,
                    network.nodes.all()
                )
        return json_data

    def read(self, request, network_id):
        try:
            network = Network.objects.get(id=network_id)
            return NetworkHandler.render(network)
        except Network.DoesNotExist:
            return rc.NOT_FOUND


class NetworkCollectionHandler(BaseHandler):

    allowed_methods = ('GET', 'POST')
    model = Network

    @validate_json(NetworkCreationForm)
    def create(self, request):
        data = request.form.cleaned_data

        try:
            release = Network.objects.get(
                name=data['name'],
                network=data['network']
            )
            return rc.DUPLICATE_ENTRY
        except Network.DoesNotExist:
            pass

        nw = Network(
            name=data['name'],
            network=data['network'],
            release=data['release'],
            access=data['access'],
            range_l=data['range_l'],
            range_h=data['range_h'],
            gateway=data['gateway'],
            vlan_id=data['vlan_id']
        )
        nw.save()

        return NetworkHandler.render(nw)

    def read(self, request):
        return map(
            NetworkHandler.render,
            Network.objects.all()
        )
