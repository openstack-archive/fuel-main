define(function() {
    var models = {};
    var collections = {};

    models.Release = Backbone.Model.extend({
        urlRoot: '/api/releases',
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
            if (attrs.mode == 'ha') {
                var redundancy = parseInt(attrs.redundancy, 10);
                if (_.isNaN(redundancy)) {
                    errors.redundancy = 'Please enter integer number';
                } else if (redundancy < 2 || redundancy > 9) {
                    errors.redundancy = 'Please enter number between 2 and 9';
                }
            }
            return _.isEmpty(errors) ? null : errors;
        },
        locked: function() {
            return this.get('task') && !this.get('task').get('ready');
        },
        parse: function(response) {
            response.nodes = new models.Nodes(response.nodes);
            response.nodes.cluster = this;
            response.release = new models.Release(response.release);
            response.task = response.task ? new models.Task(response.task) : null;
            return response;
        }
    });

    models.Clusters = Backbone.Collection.extend({
        model: models.Cluster,
        url: '/api/clusters',
        toJSON: function(options) {
            return this.pluck('id');
        }
    });

    models.Node = Backbone.Model.extend({
        urlRoot: '/api/nodes',
        initialize: function(attrs) {
            this.set('roles', new models.Roles(attrs.roles));
            this.set('new_roles', new models.Roles(attrs.new_roles));
        },
        parse: function(response) {
            response.roles = new models.Roles(response.roles);
            response.new_roles = new models.Roles(response.new_roles);
            return response;
        },
        fullProductName: function() {
            return (this.get('manufacturer') ? this.get('manufacturer') + ' ' + this.get('platform_name') : this.get('platform_name')) || 'Unknown Platform';
        },
        resource: function(resourceName) {
            return this.get('info')[resourceName];
        }
    });

    models.Nodes = Backbone.Collection.extend({
        model: models.Node,
        url: '/api/nodes',
        toJSON: function(options) {
            return this.pluck('id');
        },
        resources: function(resourceName) {
            var resources = this.map(function(node) {return node.resource(resourceName)});
            return _.reduce(resources, function(sum, n) {return sum + n}, 0);
        }
    });

    models.Role = Backbone.Model.extend({
        urlRoot: '/api/roles'
    });

    models.Roles = Backbone.Collection.extend({
        model: models.Role,
        url: '/api/roles'
    });

    return models;
});
