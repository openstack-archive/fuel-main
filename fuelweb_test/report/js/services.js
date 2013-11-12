'use strict';

/* Services */

angular.module('testresultServices', ['ngResource']).
    factory('TestResult', function ($resource) {
        return $resource('data/data.json', {}, {
            query: {method: 'GET', params: {}, isArray: true}
        });
    });