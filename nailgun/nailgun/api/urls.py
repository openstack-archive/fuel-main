from django.conf.urls import patterns, include, url
from piston.resource import Resource

from nailgun.api.handlers import ClusterCollectionHandler, ClusterHandler, \
                     NodeCollectionHandler, NodeHandler, \
                     NetworkHandler, NetworkCollectionHandler, \
                     RoleCollectionHandler, RoleHandler, \
                     ReleaseCollectionHandler, ReleaseHandler, \
                     ClusterChangesHandler, \
                     DeploymentTypeCollectionHandler, \
                     DeploymentTypeHandler, \
                     TaskHandler
from nailgun.api.handlers import ComCollectionHandler
from nailgun.api.handlers import ComHandler
from nailgun.api.handlers import PointCollectionHandler
from nailgun.api.handlers import PointHandler
from nailgun.api.handlers import EndPointCollectionHandler


class JsonResource(Resource):
    def determine_emitter(self, request, *args, **kwargs):
        return 'json'


urlpatterns = patterns('',
    url(r'^clusters/?$',
        JsonResource(ClusterCollectionHandler),
        name='cluster_collection_handler'),
    url(r'^clusters/(?P<cluster_id>\d+)/?$',
        JsonResource(ClusterHandler),
        name='cluster_handler'),
    url(r'^nodes/?$',
        JsonResource(NodeCollectionHandler),
        name='node_collection_handler'),
    url(r'^nodes/(?P<node_id>[\dA-F]{12})/?$',
        JsonResource(NodeHandler),
        name='node_handler'),
    url(r'^networks/?$',
        JsonResource(NetworkCollectionHandler),
        name='network_collection_handler'),
    url(r'^networks/(?P<network_id>\d+)/?$',
        JsonResource(NetworkHandler),
        name='network_handler'),
    url(r'^clusters/(?P<cluster_id>\d+)/changes/?$',
        JsonResource(ClusterChangesHandler),
        name='cluster_changes_handler'),
    url(r'^tasks/(?P<task_id>[\da-f\-]{36})/?$',
        JsonResource(TaskHandler),
        name='task_handler'),
    url(r'^roles/?$',
        JsonResource(RoleCollectionHandler),
        name='role_collection_handler'),
    url(r'^roles/(?P<role_id>\d+)/?$',
        JsonResource(RoleHandler),
        name='role_handler'),
    url(r'^coms/?$',
        JsonResource(ComCollectionHandler),
        name='com_collection_handler'),
    url(r'^coms/(?P<component_id>\d+)/?$',
        JsonResource(ComHandler),
        name='com_handler'),
    url(r'^points/?$',
        JsonResource(PointCollectionHandler),
        name='point_collection_handler'),
    url(r'^points/(?P<point_id>\d+)/?$',
        JsonResource(PointHandler),
        name='point_handler'),
    url(r'^endpoints/(?P<node_id>[\dA-F]{12})/(?P<component_name>\w+)/?$',
        JsonResource(EndPointCollectionHandler),
        name='endpoint_handler'),
    url(r'^endpoints/?$',
        JsonResource(EndPointCollectionHandler),
        name='endpoint_collection_handler'),
    url(r'^releases/?$',
        JsonResource(ReleaseCollectionHandler),
        name='release_collection_handler'),
    url(r'^releases/(?P<release_id>\d+)/?$',
        JsonResource(ReleaseHandler),
        name='release_handler'),
    url(r'^clusters/(?P<cluster_id>\d+)/deployment_types/?$',
        JsonResource(DeploymentTypeCollectionHandler),
        name='deployment_type_collection_handler'),
    url(r'^clusters/(?P<cluster_id>\d+)/deployment_types/' \
        r'(?P<deployment_type_id>\w+)/?$',
        JsonResource(DeploymentTypeHandler),
        name='deployment_type_handler'),
)
