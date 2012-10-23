requirejs.config({
    baseUrl: 'static',
    urlArgs: '_=' +  (new Date()).getTime(),
    paths: {
        jquery: 'js/libs/jquery-1.7.2.min',
        underscore: 'js/libs/underscore-min',
        backbone: 'js/libs/backbone-min',
        'backbone-model-update': 'js/libs/backbone-model-update',
        bootstrap: 'js/libs/bootstrap.min',
        text: 'js/libs/text',
        app: 'js/app',
        models: 'js/models',
        collections: 'js/collections',
        views: 'js/views'
    },
    shim: {
        underscore: {
            exports: '_'
        },
        backbone: {
            deps: ['underscore', 'jquery'],
            exports: 'Backbone'
        },
        'backbone-model-update': {
            deps: ['backbone']
        },
        bootstrap: {
            deps: ['jquery']
        },
        app: {
            deps: ['jquery', 'underscore', 'backbone', 'backbone-model-update', 'bootstrap']
        }
    }
});

require(['app'], function (app) {
    'use strict';
    $(document).ready(app.initialize);
});
