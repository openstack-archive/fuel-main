define(function() {
    'use strict';

    var models = {};
    var collections = {};

    models.Release = Backbone.Model.extend({
        constructorName: 'Release',
        urlRoot: '/api/releases'
    });

    models.Releases = Backbone.Collection.extend({
        constructorName: 'Releases',
        model: models.Release,
        url: '/api/releases'
    });

    models.Cluster = Backbone.Model.extend({
        constructorName: 'Cluster',
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
            return this.get('nodes').hasChanges();
        },
        canChangeMode: function() {
            return !this.task('deploy', 'running') && (this.get('mode') == 'ha' || !this.get('nodes').nodesAfterDeployment().length);
        },
        canChangeType: function(type) {
            var canCheck = true;
            var cluster = this;
            var clusterTypesToNodesRoles = {'both': [], 'compute': ['storage'], 'storage': ['compute'], 'singlenode': ['compute', 'storage']};
            _.each(clusterTypesToNodesRoles[type], function(nodeRole) {
                if (_.filter(cluster.get('nodes').nodesAfterDeployment(), function(node) {return node.get('role') == nodeRole;}).length) {
                    canCheck = false;
                }
            });
            if (type == 'singlenode' && _.where(cluster.get('nodes').nodesAfterDeployment(), {'role': 'controller'}) > 1) {
                canCheck = false;
            }
            return canCheck;
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
        constructorName: 'Clusters',
        model: models.Cluster,
        url: '/api/clusters'
    });

    models.Node = Backbone.Model.extend({
        constructorName: 'Node',
        urlRoot: '/api/nodes',
        fullProductName: function() {
            return (this.get('manufacturer') ? this.get('manufacturer') + ' ' + this.get('platform_name') : this.get('platform_name')) || 'Unknown Platform';
        },
        resource: function(resourceName) {
            return this.get('info')[resourceName];
        }
    });

    models.Nodes = Backbone.Collection.extend({
        constructorName: 'Nodes',
        model: models.Node,
        url: '/api/nodes',
        hasChanges: function() {
            return !!this.filter(function(node) {
                return node.get('pending_addition') || node.get('pending_deletion');
            }).length;
        },
        currentNodes: function() {
            return this.filter(function(node) {return !node.get('pending_addition');});
        },
        nodesAfterDeployment: function() {
            return this.filter(function(node) {return node.get('pending_addition') || !node.get('pending_deletion');});
        },
        resources: function(resourceName) {
            var resources = this.map(function(node) {return node.resource(resourceName);});
            return _.reduce(resources, function(sum, n) {return sum + n;}, 0);
        }
    });

    models.Task = Backbone.Model.extend({
        constructorName: 'Task',
        urlRoot: '/api/tasks'
    });

    models.Tasks = Backbone.Collection.extend({
        constructorName: 'Tasks',
        model: models.Task,
        url: '/api/tasks',
        toJSON: function(options) {
            return this.pluck('id');
        }
    });

    models.Notification = Backbone.Model.extend({
        urlRoot: '/api/notifications'
    });

    models.Notifications = Backbone.Collection.extend({
        model: models.Notification,
        url: '/api/notifications',
        toJSON: function(options) {
            return this.pluck('id');
        }
    });

    models.Settings = Backbone.Model.extend({
        constructorName: 'Settings',
        urlRoot: '/api/clusters/'
    });

    models.Network = Backbone.Model.extend({
        constructorName: 'Network',
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
        constructorName: 'Networks',
        model: models.Network,
        url: '/api/networks'
    });

    return models;
});
