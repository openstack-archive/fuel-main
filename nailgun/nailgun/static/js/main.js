requirejs.config({
    baseUrl: 'static',
    paths: {
        jquery: 'js/libs/jquery-1.7.2.min',
        underscore: 'js/libs/underscore-min',
        backbone: 'js/libs/backbone-min',
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
        bootstrap: {
            deps: ['jquery']
        },
        app: {
            deps: ['jquery', 'underscore', 'backbone', 'bootstrap']
        }
    }
});

require(['app'], function (app) {
    $(document).ready(app.initialize);
});
