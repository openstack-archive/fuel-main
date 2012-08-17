import os
import copy
import re
import celery
import ipaddr
import json

from piston.handler import BaseHandler, HandlerMetaClass
from piston.utils import rc, validate
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.db import models

from nailgun.models import Cluster
from nailgun.models import Release
from nailgun.models import Role
from nailgun.models import Com
from nailgun.models import Point
from nailgun.models import EndPoint
from nailgun.models import Network
from nailgun.models import Node
from nailgun.models import Task

from nailgun.deployment_types import deployment_types
from nailgun.api.validators import validate_json, validate_json_list
from nailgun.api.forms import ClusterForm
from nailgun.api.forms import ClusterCreationForm
from nailgun.api.forms import RoleFilterForm
from nailgun.api.forms import RoleCreateForm
from nailgun.api.forms import PointFilterForm
from nailgun.api.forms import PointUpdateForm
from nailgun.api.forms import PointCreateForm
from nailgun.api.forms import ComFilterForm
from nailgun.api.forms import ComCreateForm
from nailgun.api.forms import NodeCreationForm
from nailgun.api.forms import NodeFilterForm
from nailgun.api.forms import NodeForm
from nailgun.api.forms import ReleaseCreationForm
from nailgun.api.forms import NetworkCreationForm

from nailgun import tasks
import nailgun.api.validators as vld

from nailgun.helpers import DeployManager
from nailgun.helpers import DeployDriver

import logging


logger = logging.getLogger(__name__)


handlers = {}


class HandlerRegistrator(HandlerMetaClass):
    def __init__(cls, name, bases, dct):
        super(HandlerRegistrator, cls).__init__(name, bases, dct)
        if hasattr(cls, 'model'):
            key = cls.model.__name__
            if key in handlers:
                raise Exception("Handler for %s already registered" % key)
            handlers[key] = cls


class JSONHandler(BaseHandler):
    """
    Basic JSON handler
    """
    __metaclass__ = HandlerRegistrator

    fields = None

    @classmethod
    def render(cls, item, fields=None):
        json_data = {}
        use_fields = fields if fields else cls.fields

        if not use_fields:
            raise ValueError("No fields for serialize")
        for field in use_fields:
            if isinstance(field, (tuple,)):

                logger.debug("rendering: field is a tuple: %s" % str(field))
                if field[1] == '*':
                    subfields = None
                else:
                    subfields = field[1:]

                value = getattr(item, field[0])
                if value is None:
                    pass
                elif value.__class__.__name__ in ('ManyRelatedManager',
                                                'RelatedManager'):
                    try:
                        handler = handlers[value.model.__name__]
                        json_data[field[0]] = [
                            handler.render(o, fields=subfields) \
                                for o in value.all()]
                    except KeyError:
                        raise Exception("No handler for %s" % \
                                            value.model.__name__)

                elif value.__class__.__name__ in handlers:
                    handler = handlers[value.__class__.__name__]
                    json_data[field[0]] = handler.render(value,
                                                         fields=subfields)
                else:
                    json_data[field[0]] = value.id

            else:
                value = getattr(item, field)

                if value is None:
                    pass
                elif value.__class__.__name__ in ('ManyRelatedManager',
                                                  'RelatedManager',):
                    json_data[field] = [getattr(o, 'id') \
                                            for o in value.all()]
                elif value.__class__.__name__ in handlers:
                    json_data[field] = value.id
                else:
                    json_data[field] = value

        return json_data


class TaskHandler(JSONHandler):

    allowed_methods = ('GET',)
    model = Task

    @classmethod
    def render(cls, task, fields=None):
        result = {
            'task_id': task.pk,
            'name': task.name,
            'ready': task.ready,
        }
        errors = task.errors
        if len(errors):
            result['error'] = '; '.join(map(lambda e: e.__str__(), errors))

        return result

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

        logger.debug("Cluster changes: Checking if another task is running")
        if cluster.task:
            if cluster.task.ready:
                cluster.task.delete()
            else:
                response = rc.DUPLICATE_ENTRY
                response.content = "Another task is running"
                return response

        logger.debug("Cluster changes: Updating node roles")
        for node in cluster.nodes.filter(redeployment_needed=True):
            node.roles = node.new_roles.all()
            node.new_roles.clear()
            node.redeployment_needed = False
            node.save()

        logger.debug("Cluster changes: Updating node networks")
        for nw in cluster.release.networks.all():
            for node in cluster.nodes.all():
                nw.update_node_network_info(node)

        logger.debug("Cluster changes: Trying to instantiate cluster")

        dm = DeployManager(cluster_id)
        dm.clean_cluster()
        dm.instantiate_cluster()

        logger.debug("Cluster changes: Trying to deploy cluster")
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


class DeploymentTypeCollectionHandler(BaseHandler):

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

    def update(self, request, cluster_id, deployment_type_id):
        try:
            cluster = Cluster.objects.get(id=cluster_id)
            deployment_type = deployment_types[deployment_type_id]
        except ObjectDoesNotExist:
            return rc.NOT_FOUND

        deployment_type.assign_roles(cluster)

        return {}


class EndPointCollectionHandler(BaseHandler):
    allowed_methods = ('GET',)

    def read(self, request, node_id=None, component_name=None):
        if not node_id or not component_name:
            return map(EndPointHandler.render,
                       EndPoint.objects.all())

        try:
            node = Node.objects.get(id=node_id)
            component = Com.objects.get(
                name=component_name,
                release=node.cluster.release
                )
            dd = DeployDriver(node, component)
            return dd.deploy_data()
        except:
            return rc.NOT_FOUND


class EndPointHandler(JSONHandler):
    model = EndPoint

    @classmethod
    def render(cls, endpoint):
        return endpoint.data


class ClusterCollectionHandler(BaseHandler):

    allowed_methods = ('GET', 'POST')

    def read(self, request):
        json_data = map(
            ClusterHandler.render,
            Cluster.objects.all()
        )
        return json_data

    @validate_json(ClusterCreationForm)
    def create(self, request):
        data = request.form.cleaned_data

        try:
            cluster = Cluster.objects.get(
                name=data['name']
            )
            return rc.DUPLICATE_ENTRY
        except Cluster.DoesNotExist:
            pass

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
            'floating': 400,
            'fixed': 500,
            'admin': 100
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
                range_l=str(new_network[3]),
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
    fields = ('id', 'name',
              ('nodes', '*'),
              ('release', '*'), 'task')

    def read(self, request, cluster_id):
        logger.debug("Cluster reading: id: %s" % cluster_id)
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
    fields = ('id', 'name', 'info', 'status', 'mac', 'fqdn', 'ip',
              'manufacturer', 'platform_name', 'redeployment_needed',
              ('roles', '*'), ('new_roles', '*'), 'os_platform')

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


class PointCollectionHandler(BaseHandler):

    allowed_methods = ('GET', 'POST')

    @validate(PointFilterForm, 'GET')
    def read(self, request):
        logger.debug("Getting points from data: %s" % \
                         str(request.form.data))
        if 'release' in request.form.data:
            points = Point.objects.filter(
                release__id=request.form.cleaned_data['release']
                )
        else:
            points = Point.objects.all()
        return map(PointHandler.render, points)

    @validate_json(PointCreateForm)
    def create(self, request):
        data = request.form.cleaned_data
        logger.debug("Creating Point from data: %s" % str(data))

        try:
            point = Point.objects.get(
                name=data['name'],
                release=data['release']
            )
            return rc.DUPLICATE_ENTRY
        except Point.DoesNotExist:
            pass

        point = Point(
            name=data['name'],
            release=data['release']
            )

        if 'scheme' in data:
            point.scheme = data['scheme']
        else:
            point.scheme = {}
        point.save()

        return PointHandler.render(point)


class PointHandler(JSONHandler):

    allowed_methods = ('GET', 'PUT')
    model = Point

    fields = ('id', 'name', 'scheme', ('release', 'name'),
              ('required_by', 'name'),
              ('provided_by', 'name'))

    def read(self, request, point_id):
        try:
            return PointHandler.render(Point.objects.get(id=point_id))
        except ObjectDoesNotExist:
            return rc.NOT_FOUND

    @validate_json(PointUpdateForm)
    def update(self, request, point_id):
        data = request.form.cleaned_data
        logger.debug("Updating Point from data: %s" % str(data))

        try:
            point = Point.objects.get(id=point_id)
        except ObjectDoesNotExist:
            return rc.NOT_FOUND

        if data.get('scheme', None):
            point.scheme = data['scheme']

        point.save()
        return PointHandler.render(point)


class ComCollectionHandler(BaseHandler):
    allowed_methods = ('GET', 'POST')

    @validate(ComFilterForm, 'GET')
    def read(self, request):
        logger.debug("Getting components from data: %s" % \
                         str(request.form.data))
        if 'release' in request.form.data:
            components = Com.objects.filter(
                release__id=request.form.cleaned_data['release']
                )
        else:
            components = Com.objects.all()
        return map(ComHandler.render, components)

    @validate_json(ComCreateForm)
    def create(self, request):
        data = request.form.cleaned_data
        logger.debug("Creating Com from data: %s" % str(data))

        try:
            component = Com.objects.get(
                name=data['name'],
                release=data['release']
            )
            return rc.DUPLICATE_ENTRY
        except Com.DoesNotExist:
            pass

        component = Com(
            name=data['name'],
            release=data['release']
            )

        component.deploy = data['deploy']
        component.save()

        if data.get('requires', None):
            for point_name in data['requires']:
                try:
                    point = Point.objects.get(
                        name=point_name,
                        release=data['release']
                        )
                except ObjectDoesNotExist:
                    return rc.NOT_FOUND
                else:
                    component.requires.add(point)

        if data.get('provides', None):
            for point_name in data['provides']:
                try:
                    point = Point.objects.get(
                        name=point_name,
                        release=data['release']
                        )
                except ObjectDoesNotExist:
                    return rc.NOT_FOUND
                else:
                    component.provides.add(point)

        component.save()
        return ComHandler.render(component)


class ComHandler(JSONHandler):
    allowed_methods = ('GET',)
    model = Com

    fields = ('id', 'name', 'deploy', ('release', 'name'),
              ('requires', 'name'), ('provides', 'name'),
              ('roles', 'name'))

    def read(self, request, component_id):
        try:
            return ComHandler.render(Com.objects.get(id=component_id))
        except ObjectDoesNotExist:
            return rc.NOT_FOUND


class RoleCollectionHandler(BaseHandler):

    allowed_methods = ('GET', 'POST')

    @validate(RoleFilterForm, 'GET')
    def read(self, request):
        if 'release_id' in request.form.data:
            return map(
                RoleHandler.render,
                Role.objects.filter(
                    release__id=request.form.data['release_id']
                    )
                )

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

    @validate_json(RoleCreateForm)
    def create(self, request):
        data = request.form.cleaned_data
        logger.debug("Creating Role from data: %s" % str(data))

        try:
            role = Role.objects.get(
                name=data['name'],
                release=data['release']
            )
            return rc.DUPLICATE_ENTRY
        except Role.DoesNotExist:
            pass

        role = Role(
            name=data['name'],
            release=data['release']
            )

        role.save()

        if data.get('components', None):
            for component_name in data['components']:
                try:
                    component = Com.objects.get(
                        name=component_name,
                        release=data['release']
                        )
                except ObjectDoesNotExist:
                    return rc.NOT_FOUND
                else:
                    role.components.add(component)

        role.save()
        return RoleHandler.render(role)


class RoleHandler(JSONHandler):

    allowed_methods = ('GET',)
    model = Role
    fields = ('id', 'name', ('release', 'id', 'name'),
              ('components', 'name'))

    def read(self, request, role_id):
        try:
            return RoleHandler.render(Role.objects.get(id=role_id))
        except ObjectDoesNotExist:
            return rc.NOT_FOUND


class ReleaseCollectionHandler(BaseHandler):

    logger.warning("Trying to add release")

    allowed_methods = ('GET', 'POST')
    model = Release

    def read(self, request):
        return map(ReleaseHandler.render, Release.objects.all())

    @validate_json(ReleaseCreationForm)
    def create(self, request):
        data = request.form.cleaned_data
        logger.debug("Creating release from data: %s" % str(data))
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

        return ReleaseHandler.render(release)


class ReleaseHandler(JSONHandler):

    allowed_methods = ('GET', 'DELETE')
    model = Release
    fields = ('id', 'name', 'version', 'description', 'networks_metadata',
              ('roles', 'name'), ('components', 'name'),
              ('points', 'name'))

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
            'vlan_id', 'range_l', 'range_h', 'gateway',
            'release', 'nodes',
            'release_id')

    def read(self, request, network_id):
        try:
            network = Network.objects.get(id=network_id)
            return NetworkHandler.render(network)
        except Network.DoesNotExist:
            return rc.NOT_FOUND


class NetworkCollectionHandler(BaseHandler):

    allowed_methods = ('GET', 'POST')

    def read(self, request):
        return map(NetworkHandler.render, Network.objects.all())

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
