from django.conf.urls import patterns, include, url
from piston.resource import Resource

from handlers import EnvironmentHandler, NodeHandler, RoleHandler, \
                     ConfigHandler, TaskHandler


class JsonResource(Resource):
    def determine_emitter(self, request, *args, **kwargs):
        return 'json'


environment_handler = JsonResource(EnvironmentHandler)
node_handler = JsonResource(NodeHandler)
role_handler = JsonResource(RoleHandler)
config_handler = JsonResource(ConfigHandler)
task_handler = JsonResource(TaskHandler)

urlpatterns = patterns('',
    url(r'^environments/?$', environment_handler),
    url(r'^environments/(?P<environment_id>\d+)/?$', environment_handler),
    url(r'^environments/(?P<environment_id>\d+)/chef-config/?$',
        config_handler),
    url(r'^environments/(?P<environment_id>\d+)/nodes/?$', node_handler),
    url(r'^environments/(?P<environment_id>\d+)/nodes/'
        r'(?P<node_name>[\w\.\-]+)/?$', node_handler),
    url(r'^nodes/?$', node_handler, {'environment_id': None}),
    url(r'^nodes/(?P<node_name>[\w\.\-]+)/?$', node_handler,
        {'environment_id': None}),
    url(r'^environments/(?P<environment_id>\d+)/nodes/'
        r'(?P<node_name>[\w\.\-]+)/roles/?$', role_handler),
    url(r'^environments/(?P<environment_id>\d+)/nodes/'
        r'(?P<node_name>[\w\.\-]+)/roles/(?P<role_id>\w+)/?$', role_handler),
    url(r'^tasks/(?P<task_id>[\da-f\-]{36})/?$', task_handler),
)
