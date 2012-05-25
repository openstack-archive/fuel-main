from django.conf.urls import patterns, include, url
from piston.resource import Resource

from handlers import EnvironmentCollectionHandler, EnvironmentHandler, \
                     NodeCollectionHandler, NodeHandler, \
                     RoleCollectionHandler, RoleHandler, \
                     ConfigHandler, \
                     TaskCollectionHandler


class JsonResource(Resource):
    def determine_emitter(self, request, *args, **kwargs):
        return 'json'


urlpatterns = patterns('',
    url(r'^environments/?$', JsonResource(EnvironmentCollectionHandler)),
    url(r'^environments/(?P<environment_id>\d+)/?$',
        JsonResource(EnvironmentHandler)),
    url(r'^environments/(?P<environment_id>\d+)/chef-config/?$',
        JsonResource(ConfigHandler)),
    url(r'^environments/(?P<environment_id>\d+)/nodes/?$',
        JsonResource(NodeCollectionHandler)),
    url(r'^environments/(?P<environment_id>\d+)/nodes/'
        r'(?P<node_name>[\w\.\-]+)/?$',
        JsonResource(NodeHandler)),
    url(r'^nodes/?$',
        JsonResource(NodeCollectionHandler), {'environment_id': None}),
    url(r'^nodes/(?P<node_name>[\w\.\-]+)/?$',
        JsonResource(NodeHandler), {'environment_id': None}),
    url(r'^environments/(?P<environment_id>\d+)/nodes/'
        r'(?P<node_name>[\w\.\-]+)/roles/?$',
        JsonResource(RoleCollectionHandler)),
    url(r'^environments/(?P<environment_id>\d+)/nodes/'
        r'(?P<node_name>[\w\.\-]+)/roles/(?P<role_id>\w+)/?$',
        JsonResource(RoleHandler)),
    url(r'^tasks/(?P<task_id>[\da-f\-]{36})/?$',
        JsonResource(TaskCollectionHandler)),
)
