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
        url: '/api/releases',
        comparator: function(release) {
            return release.id;
        }
    });

    models.Cluster = Backbone.Model.extend({
        constructorName: 'Cluster',
        urlRoot: '/api/clusters',
        defaults: function() {
            var defaults = {
                nodes: new models.Nodes(),
                tasks: new models.Tasks()
            };
            defaults.nodes.cluster = defaults.tasks.cluster = this;
            return defaults;
        },
        validate: function(attrs) {
            var errors = {};
            if (!$.trim(attrs.name) || $.trim(attrs.name).length == 0) {
                errors.name = 'Environment name cannot be empty';
            }
            if (!attrs.release) {
                errors.release = 'Please choose OpenStack release';
            }
            return _.isEmpty(errors) ? null : errors;
        },
        task: function(taskName, status) {
            return this.get('tasks') && this.get('tasks').find(function(task) {
                var result = false;
                if (task.get('name') == taskName) {
                    if (status) {
                        if (_.isArray(status)) {
                            result = _.contains(status, task.get('status'));
                        } else {
                            result = status == task.get('status');
                        }
                    } else {
                        result = true;
                    }
                }
                return result;
            });
        },
        hasChanges: function() {
            return this.get('nodes').hasChanges() || (this.get('changes').length && this.get('nodes').currentNodes().length);
        },
        needsRedeployment: function() {
            return this.get('nodes').where({pending_addition: false, status: 'error'}).length;
        },
        canChangeMode: function(newMode) {
            var nodes = this.get('nodes');
            return !(nodes.currentNodes().length || nodes.where({role: 'controller'}).length > 1 || (newMode && newMode == 'singlenode' && (nodes.length > 1 || (nodes.length == 1 && !nodes.where({role: 'controller'}).length))));
        },
        canChangeType: function(newType) {
            // FIXME: algorithmic complexity is very high
            var canChange;
            var nodes = this.get('nodes');
            if (!newType) {
                canChange = false;
                _.each(this.availableTypes(), function(type) {
                    if (type == this.get('type')) {return;}
                    canChange = canChange || this.canChangeType(type);
                }, this);
            } else {
                canChange = true;
                var clusterTypesToNodesRoles = {'both': [], 'compute': ['cinder'], 'cinder': ['compute']};
                _.each(clusterTypesToNodesRoles[newType], function(nodeRole) {
                    if (nodes.where({role: nodeRole}).length) {
                        canChange = false;
                    }
                }, this);
                canChange = canChange && !nodes.currentNodes().length;
            }
            return canChange;
        },
        canAddNodes: function(role) {
            // forbid adding when tasks are running
            if (this.task('deploy', 'running') || this.task('verify_networks', 'running')) {
                return false;
            }
            // forbid add more than 1 controller in simple mode
            if (role == 'controller' && this.get('mode') != 'ha' && _.filter(this.get('nodes').nodesAfterDeployment(), function(node) {return node.get('role') == role;}).length >= 1) {
                return false;
            }
            return true;
        },
        canDeleteNodes: function(role) {
            // forbid deleting when tasks are running
            if (this.task('deploy', 'running') || this.task('verify_networks', 'running')) {
                return false;
            }
            // forbid deleting when there is nothing to delete
            if (!_.filter(this.get('nodes').nodesAfterDeployment(), function(node) {return node.get('role') == role;}).length) {
                return false;
            }
            return true;
        },
        availableModes: function() {
            return ['multinode', 'ha'];
        },
        availableTypes: function() {
            return ['compute', 'both'];
        },
        availableRoles: function() {
            var roles = ['controller'];
            if (this.get('mode') != 'singlenode') {
                if (this.get('type') == 'both') {
                    roles.push('compute', 'cinder');
                } else {
                    roles.push(this.get('type'));
                }
            }
            return roles;
        },
        parse: function(response) {
            response.release = new models.Release(response.release);
            return response;
        },
        fetchRelated: function(related, options) {
            return this.get(related).fetch(_.extend({data: {cluster_id: this.id}}, options));
        }
    });

    models.Clusters = Backbone.Collection.extend({
        constructorName: 'Clusters',
        model: models.Cluster,
        url: '/api/clusters',
        comparator: function(cluster) {
            return cluster.id;
        }
    });

    models.Node = Backbone.Model.extend({
        constructorName: 'Node',
        urlRoot: '/api/nodes',
        volumeGroupsByRoles: function(role) {
            var volumeGroups =  {
                controller: ['os'],
                compute: ['os', 'vm'],
                storage: ['os', 'cinder']
            };
            return volumeGroups[role];
        },
        resource: function(resourceName) {
            var resource = 0;
            try {
                if (resourceName == 'cores') {
                    resource = this.get('meta').cpu.total;
                } else if (resourceName == 'hdd') {
                    var hdd = 0;
                    _.each(this.get('meta').disks, function(disk) {
                        if (_.isNumber(disk.size)) {
                            hdd += disk.size;
                        }
                    });
                    resource = hdd;
                } else if (resourceName == 'ram') {
                    resource = this.get('meta').memory.total / Math.pow(1024, 3);
                }
            } catch (e) {}
            if (_.isNaN(resource)) {
                resource = 0;
            }
            return resource;
        }
    });

    models.Nodes = Backbone.Collection.extend({
        constructorName: 'Nodes',
        model: models.Node,
        url: '/api/nodes',
        comparator: function(node) {
            return node.id;
        },
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
        },
        comparator: function(task) {
            return task.id;
        }
    });

    models.Notification = Backbone.Model.extend({
        constructorName: 'Notification',
        urlRoot: '/api/notifications'
    });

    models.Notifications = Backbone.Collection.extend({
        constructorName: 'Notifications',
        model: models.Notification,
        url: '/api/notifications',
        comparator: function(notification) {
            return notification.id;
        }
    });

    models.Settings = Backbone.Model.extend({
        constructorName: 'Settings',
        urlRoot: '/api/clusters/',
        isNew: function() {
            return false;
        }
    });

    models.Disk = Backbone.Model.extend({
        constructorName: 'Disk',
        urlRoot: '/api/nodes/',
        validate: function(attrs, options) {
            var errors = [];
            var volume = _.find(attrs.volumes, {vg: options.group});
            if (_.isNaN(volume.size) || volume.size > options.unallocated) {
                errors.push(volume.vg);
            }
            return _.isEmpty(errors) ? null : errors;
        }
    });

    models.Disks = Backbone.Collection.extend({
        constructorName: 'Disks',
        model: models.Disk,
        url: '/api/nodes/',
        comparator: function(disk) {
            return disk.id;
        }
    });

    models.Network = Backbone.Model.extend({
        constructorName: 'Network',
        urlRoot: '/api/networks',
        validate: function(attrs) {
            var errors = {};
            var match;
            if (_.isString(attrs.cidr)) {
                var cidrRegexp = /^(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\/([1-9]|[1-2]\d|3[0-2])$/;
                match = attrs.cidr.match(cidrRegexp);
                if (match) {
                    var prefix = parseInt(match[1], 10);
                    if (prefix < 2) {
                        errors.cidr = 'Network is too large';
                    }
                    if (prefix > 30) {
                        errors.cidr = 'Network is too small';
                    }
                } else {
                    errors.cidr = 'Invalid CIDR';
                }
            } else {
                errors.cidr = 'Invalid CIDR';
            }
            if (_.isString(attrs.vlan_start)) {
                match = attrs.vlan_start.match(/^[0-9]+$/);
                if (match) {
                    attrs.vlan_start = parseInt(match[0], 10);
                } else {
                    errors.vlan_start = 'Invalid VLAN ID';
                }
            }
            if (_.isNaN(attrs.vlan_start) || !_.isNumber(attrs.vlan_start) || attrs.vlan_start < 1 || attrs.vlan_start > 4094) {
                errors.vlan_start = 'Invalid VLAN ID';
            }
            if (_.isString(attrs.amount)) {
                match = attrs.amount.match(/^[0-9]+$/);
                if (match) {
                    attrs.amount = parseInt(match[0], 10);
                } else {
                    errors.amount = 'Invalid amount of networks';
                }
            }
            if (!attrs.amount || (attrs.amount && (!_.isNumber(attrs.amount) || attrs.amount < 1))) {
                errors.amount = 'Invalid amount of networks';
            }
            if (attrs.amount && attrs.amount > 4095 - attrs.vlan_start) {
                errors.amount = 'Unable to fit requested amount of networks to available VLANs. Lower VLAN start range or amount of networks.';
            }
            return _.isEmpty(errors) ? null : errors;
        }
    });

    models.Networks = Backbone.Collection.extend({
        constructorName: 'Networks',
        model: models.Network,
        url: '/api/networks',
        comparator: function(network) {
            return network.id;
        }
    });

    models.LogSource = Backbone.Model.extend({
        constructorName: 'LogSource',
        urlRoot: '/api/logs/sources'
    });

    models.LogSources = Backbone.Collection.extend({
        constructorName: 'LogSources',
        model: models.LogSource,
        url: '/api/logs/sources'
    });

    return models;
});
