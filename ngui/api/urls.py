from django.conf.urls import patterns, include, url
from piston.resource import Resource
from handlers import EnvironmentHandler, NodeHandler

environment_handler = Resource(EnvironmentHandler)
node_handler = Resource(NodeHandler)

urlpatterns = patterns('',
    url(r'^environments/?$', environment_handler),
    url(r'^environments/(?P<environment_id>\d+)$', environment_handler),
    url(r'^environments/(?P<environment_id>\d+)/nodes/?$', node_handler),
    url(r'^environments/(?P<environment_id>\d+)/nodes/(?P<node_id>\d+)$', node_handler),
)
