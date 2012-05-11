from django.conf.urls import patterns, include, url
from ngui.views import index

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', index, name='index'),
    (r'^api/', include('api.urls')),
)
