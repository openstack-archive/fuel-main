define(function() {
    var models = {};
    var collections = {};

    models.Release = Backbone.Model.extend({
        urlRoot: '/api/releases',
        defaults: {
            name: null,
            version: null,
            description: null
        },
        initialize: function(attrs) {
            this.set('roles', new models.Roles(attrs.roles));
        }
    });

    models.Releases = Backbone.Collection.extend({
        model: models.Release,
        url: '/api/releases'
    });

    models.Cluster = Backbone.Model.extend({
        urlRoot: '/api/clusters',
        defaults: {
            name: null
        },
        validate: function(attrs) {
            var errors = {};
            if (!attrs.name || attrs.name.length == 0) {
                errors.name = 'Cluster name cannot be empty';
            } else if (attrs.name.length > 100) {
                errors.name = 'Cluster name is too long';
            }
            if (!attrs.release) {
                errors.release = 'Please choose OpenStack release';
            }
            return _.isEmpty(errors) ? null : errors;
        },
        parse: function(response) {
            response.nodes = new models.Nodes(response.nodes);
            response.release = new models.Release(response.release);
            return response;
        }
    });

    models.Clusters = Backbone.Collection.extend({
        model: models.Cluster,
        url: '/api/clusters'
    });

    models.Node = Backbone.Model.extend({
        urlRoot: '/api/nodes',
        defaults: {
            name: null,
            status: null,
            metadata: null
        },
        initialize: function(attrs) {
            this.set('roles', new models.Roles(attrs.roles));
        },
        parse: function(response) {
            response.roles = new models.Roles(response.roles);
            return response;
        }
    });

    models.Nodes = Backbone.Collection.extend({
        model: models.Node,
        url: '/api/nodes',
        toJSON: function(options) {
            return this.pluck('id');
        }
    });

    models.Cookbook = Backbone.Model.extend({
        urlRoot: '/api/cookbooks',
        defaults: {
            name: null,
            version: null
        },
        initialize: function(attrs) {
            this.set('roles', new models.Roles(attrs.roles));
        }
    });

    models.Cookbooks = Backbone.Collection.extend({
        model: models.Cookbook
    });

    models.Role = Backbone.Model.extend({
        urlRoot: '/api/roles',
        defaults: {
            name: null
        }
    });

    models.Roles = Backbone.Collection.extend({
        model: models.Role,
        url: '/api/roles'
    });

    return models;
});
