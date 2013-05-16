requirejs.config({
    baseUrl: 'static',
    urlArgs: '_=' +  (new Date()).getTime(),
    waitSeconds: 60,
    paths: {
        jquery: 'js/libs/jquery-1.9.1',
        'jquery-checkbox': 'js/libs/jquery.checkbox',
        'jquery-timeout': 'js/libs/jquery.timeout',
        utils: 'js/utils',
        'jquery-ui': 'js/libs/jquery-ui-1.10.2.custom',
        utils: 'js/utils',
        lodash: 'js/libs/lodash',
        backbone: 'js/libs/backbone',
        coccyx: 'js/libs/coccyx',
        bootstrap: 'js/libs/bootstrap.min',
        text: 'js/libs/text',
        app: 'js/app',
        models: 'js/models',
        collections: 'js/collections',
        views: 'js/views'
    },
    shim: {
        lodash: {
            exports: '_'
        },
        backbone: {
            deps: ['lodash', 'jquery'],
            exports: 'Backbone'
        },
        coccyx: {
            deps: ['lodash', 'backbone']
        },
        bootstrap: {
            deps: ['jquery']
        },
        'jquery-checkbox': {
            deps: ['jquery']
        },
        'jquery-timeout': {
            deps: ['jquery']
        },
        'jquery-ui': {
            deps: ['jquery']
        },
        app: {
            deps: ['jquery', 'lodash', 'backbone', 'coccyx', 'bootstrap', 'jquery-checkbox', 'jquery-timeout', 'jquery-ui']
        }
    }
});

require(['app'], function (app) {
    'use strict';
    $(document).ready(app.initialize);
});
