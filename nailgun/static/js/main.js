requirejs.config({
    baseUrl: 'static',
    urlArgs: '_=' +  (new Date()).getTime(),
    waitSeconds: 60,
    paths: {
        jquery: 'js/libs/jquery-1.7.2.min',
        jqueryUIcore: 'js/libs/jquery-ui-1.9.2.custom.min',
        underscore: 'js/libs/underscore-min',
        backbone: 'js/libs/backbone-min',
        'backbone-model-update': 'js/libs/backbone-model-update',
        coccyx: 'js/libs/coccyx',
        bootstrap: 'js/libs/bootstrap.min',
        text: 'js/libs/text',
        app: 'js/app',
        models: 'js/models',
        collections: 'js/collections',
        views: 'js/views'
    },
    shim: {
        jqueryUIcore: {
            deps: ['jquery']
        },
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
        coccyx: {
            deps: ['underscore', 'backbone']
        },
        bootstrap: {
            deps: ['jquery']
        },
        app: {
            deps: ['jquery', 'jqueryUIcore', 'underscore', 'backbone', 'backbone-model-update', 'coccyx', 'bootstrap']
        }
    }
});

require(['app'], function (app) {
    'use strict';
    $(document).ready(app.initialize);
});
