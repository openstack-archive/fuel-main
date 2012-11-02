define(function() {
    'use strict';

    var models = {};
    var collections = {};

    models.Release = Backbone.Model.extend({
        urlRoot: '/api/releases'
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
                if (_.isNaN(attrs.redundancy)) {
                    errors.redundancy = 'Please enter integer number';
                } else if (attrs.redundancy < 2 || attrs.redundancy > 9) {
                    errors.redundancy = 'Please enter number between 2 and 9';
                }
            }
            return _.isEmpty(errors) ? null : errors;
        },
        task: function(taskName, status) {
            var options = {name: taskName};
            if (status) {
                options.status = status;
            }
            return this.get('tasks') && this.get('tasks').where(options)[0];
        },
        hasChanges: function() {
            return _.any(this.get('nodes').pluck('redeployment_needed'));
        },
        canChangeMode: function() {
            return !this.get('nodes').length && this.get('type') != 'singlenode';
        },
        canChangeType: function() {
            return !this.get('nodes').length;
        },
        availableModes: function() {
            return ['simple', 'ha'];
        },
        availableTypes: function() {
            return ['both', 'compute', 'storage', 'singlenode'];
        },
        availableRoles: function() {
            var roles = [];
            if (this.get('type') == 'storage') {
                roles = ['controller', 'storage'];
            } else if (this.get('type') == 'compute') {
                roles = ['controller', 'compute'];
            } else if (this.get('type') == 'singlenode') {
                roles = ['controller'];
            } else {
                roles = ['controller', 'compute', 'storage'];
            }
            return roles;
        },
        parse: function(response) {
            response.release = new models.Release(response.release);
            response.nodes = new models.Nodes(response.nodes);
            response.nodes.cluster = this;
            response.tasks = new models.Tasks(response.tasks);
            response.tasks.cluster = this;
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
            var resources = this.map(function(node) {return node.resource(resourceName);});
            return _.reduce(resources, function(sum, n) {return sum + n;}, 0);
        }
    });

    models.Task = Backbone.Model.extend({
        urlRoot: '/api/tasks'
    });

    models.Tasks = Backbone.Collection.extend({
        model: models.Task,
        url: '/api/tasks',
        toJSON: function(options) {
            return this.pluck('id');
        }
    });

    models.Settings = Backbone.Model.extend({
        urlRoot: '/api/clusters/'
    });

    models.Network = Backbone.Model.extend({
        urlRoot: '/api/networks',
        validate: function(attrs) {
            var errors = {};
            if (_.isString(attrs.cidr)) {
                var cidrRegexp = /^(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\/([1-9]|[1-2]\d|3[0-2])$/;
                var match = attrs.cidr.match(cidrRegexp);
                if (match) {
                    var prefix = parseInt(match[1], 10);
                    if (prefix < 2) {
                        errors.cidr = 'Network is too large';
                    } else if (prefix > 31) {
                        errors.cidr = 'Network is too small';
                    }
                } else {
                    errors.cidr = 'Invalid CIDR';
                }
            } else {
                errors.cidr = 'Invalid CIDR';
            }
            if (_.isNaN(attrs.vlan_id) || !_.isNumber(attrs.vlan_id) || attrs.vlan_id < 1 || attrs.vlan_id > 4094) {
                errors.vlan_id = 'Invalid VLAN ID';
            }
            return _.isEmpty(errors) ? null : errors;
        }
    });

    models.Networks = Backbone.Collection.extend({
        model: models.Network,
        url: '/api/networks'
    });

    return models;
});
