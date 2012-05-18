from django.conf.urls import patterns, include, url
from piston.resource import Resource
from handlers import EnvironmentHandler, NodeHandler, RoleHandler, ConfigHandler

class JsonResource(Resource):
    def determine_emitter(self, request, *args, **kwargs):
        return 'json'

environment_handler = JsonResource(EnvironmentHandler)
node_handler = JsonResource(NodeHandler)
role_handler = JsonResource(RoleHandler)
config_handler = JsonResource(ConfigHandler)

urlpatterns = patterns('',
    url(r'^environments/?$', environment_handler),
    url(r'^environments/(?P<environment_id>\d+)/?$', environment_handler),
    url(r'^environments/(?P<environment_id>\d+)/chef-config/?$', config_handler),
    url(r'^environments/(?P<environment_id>\d+)/nodes/?$', node_handler),
    url(r'^environments/(?P<environment_id>\d+)/nodes/(?P<node_name>[\w\.\-]+)/?$', node_handler),
    url(r'^environments/(?P<environment_id>\d+)/nodes/(?P<node_name>[\w\.\-]+)/roles/?$', role_handler),
    url(r'^environments/(?P<environment_id>\d+)/nodes/(?P<node_name>[\w\.\-]+)/roles/(?P<role_name>\w+)/?$', role_handler),
)
