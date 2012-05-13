from django.conf.urls import patterns, include, url
from nailgun.webui.views import index

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', index, name='index'),
)
