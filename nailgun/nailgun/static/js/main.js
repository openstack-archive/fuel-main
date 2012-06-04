requirejs.config({
    baseUrl: 'static',
    paths: {
        jquery: 'jquery-ui/js/jquery-1.7.1.min',
        underscore: 'js/libs/underscore-min',
        backbone: 'js/libs/backbone-min',
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
        app: {
            deps: ['jquery', 'underscore', 'backbone']
        }
    }
});

require(['app'], function (app) {
    $(document).ready(app.initialize);
});
