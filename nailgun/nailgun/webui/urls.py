from django.conf.urls import patterns, include, url
from django.conf import settings

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'django.views.static.serve',
        {
            'document_root': settings.STATIC_DOC_ROOT,
            'path': 'index.html'
        }, name='index'),
)
