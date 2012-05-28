from django.conf.urls import patterns, include, url
from piston.resource import Resource

from handlers import EnvironmentCollectionHandler, EnvironmentHandler, \
                     NodeCollectionHandler, NodeHandler, \
                     RoleCollectionHandler, RoleHandler, \
                     ConfigHandler, \
                     TaskHandler


class JsonResource(Resource):
    def determine_emitter(self, request, *args, **kwargs):
        return 'json'


urlpatterns = patterns('',
    url(r'^environments/?$',
        JsonResource(EnvironmentCollectionHandler),
        name='environment_collection_handler'),
    url(r'^environments/(?P<environment_id>\d+)/?$',
        JsonResource(EnvironmentHandler),
        name='environment_handler'),
    url(r'^nodes/?$',
        JsonResource(NodeCollectionHandler),
        name='node_collection_handler'),
    url(r'^nodes/(?P<node_id>[\da-f]{12})/?$',
        JsonResource(NodeHandler),
        name='node_handler'),
    url(r'^nodes/(?P<node_id>[\da-f]{12})/roles/?$',
        JsonResource(RoleCollectionHandler),
        name='role_collection_handler'),
    url(r'^nodes/(?P<node_id>[\da-f]{12})/roles/(?P<role_id>\w+)/?$',
        JsonResource(RoleHandler),
        name='role_handler'),
    url(r'^environments/(?P<environment_id>\d+)/chef-config/?$',
        JsonResource(ConfigHandler),
        name='config_handler'),
    url(r'^tasks/(?P<task_id>[\da-f\-]{36})/?$',
        JsonResource(TaskHandler),
        name='task_handler'),
)
