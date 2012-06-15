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
            if (_.isObject(attrs) && _.isArray(attrs.roles)) {
                this.set('roles', new models.Roles(attrs.roles));
            }
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
        initialize: function(attrs) {
            if (_.isObject(attrs) && _.isArray(attrs.nodes)) {
                this.set('nodes', new models.Nodes(attrs.nodes));
            }
        },
        parse: function(response) {
            if (_.isObject(response) && _.isArray(response.nodes)) {
                response.nodes = new models.Nodes(response.nodes);
            }
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
            if (_.isObject(attrs) && _.isArray(attrs.roles)) {
                this.set('roles', new models.Roles(attrs.roles));
            }
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
            if (_.isObject(attrs) && _.isArray(attrs.roles)) {
                this.set('roles', new models.Roles(attrs.roles));
            }
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
