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
            return this.get('tasks') && this.get('tasks').filterTasks({name: taskName, status: status})[0];
        },
        deployTask: function(status) {
            var task = this.task('check_before_deployment', status);
            if (task) {
                return task;
            }
            return this.task('deploy', status);
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
        availableRoles: function() {
            var roles = ['controller'];
            if (this.get('mode') != 'singlenode') {
                roles.push('compute', 'cinder');
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
                cinder: ['os', 'cinder']
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
        },
        getDownloadTask: function(release) {
            return this.filterTasks({name: 'download_release', status: 'running', release: release})[0];
        },
        filterTasks: function(filters) {
            return _.filter(this.models, function(task) {
                var result = false;
                if (task.get('name') == filters.name) {
                    result = true;
                    if (filters.status) {
                        if (_.isArray(filters.status)) {
                            result = _.contains(filters.status, task.get('status'));
                        } else {
                            result = filters.status == task.get('status');
                        }
                    }
                    if (filters.release) {
                        result = result && filters.release == task.get('result').release_info.release_id;
                    }
                }
                return result;
            });
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
            var errors = {};
            var volume = _.find(attrs.volumes, {vg: options.group});
            if (_.isNaN(volume.size) || volume.size < 0) {
                errors[volume.vg] = 'Invalid size';
            } else if (volume.size > options.unallocated) {
                errors[volume.vg] = 'Maximal size is ' + options.unallocated + ' GB';
            } else if (volume.size < options.min) {
                errors[volume.vg] = 'Minimal size is ' + options.min.toFixed(2) + ' GB';
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

    models.Interface = Backbone.Model.extend({
        constructorName: 'Interface',
        parse: function(response) {
            response.assigned_networks = new models.InterfaceNetworks(response.assigned_networks);
            return response;
        },
        toJSON: function(options) {
            return _.extend(this.constructor.__super__.toJSON.call(this, options), {assigned_networks: this.get('assigned_networks').toJSON()});
        }
    });

    models.Interfaces = Backbone.Collection.extend({
        constructorName: 'Interfaces',
        model: models.Interface,
        comparator: function(ifc) {
            return ifc.get('name');
        }
    });

    models.InterfaceNetwork = Backbone.Model.extend({
        constructorName: 'InterfaceNetwork'
    });

    models.InterfaceNetworks = Backbone.Collection.extend({
        constructorName: 'InterfaceNetworks',
        model: models.InterfaceNetwork
    });

    models.NodeInterfaceConfiguration = Backbone.Model.extend({
        constructorName: 'NodeInterfaceConfiguration',
        parse: function(response) {
            response.interfaces = new models.Interfaces(response.interfaces);
            return response;
        }
    });

    models.NodeInterfaceConfigurations = Backbone.Collection.extend({
        url: '/api/nodes/interfaces',
        constructorName: 'NodeInterfaceConfigurations',
        model: models.NodeInterfaceConfiguration
    });

    models.Network = Backbone.Model.extend({
        constructorName: 'Network',
        getAttributes: function() {
            var attributes = {
                'floating': ['ip_ranges', 'vlan_start'],
                'public': ['ip_ranges', 'vlan_start', 'netmask', 'gateway'],
                'management': ['cidr', 'vlan_start'],
                'storage': ['cidr', 'vlan_start'],
                'fixed': ['cidr', 'amount', 'network_size', 'vlan_start']
            };
            return attributes[this.get('name')] || ['vlan_start'];
        },
        validateIP: function(value) {
            var ipRegexp = /^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$/;
            return _.isString(value) && !value.match(ipRegexp);
        },
        validateNetmask: function(value) {
            var valid_values = {0:1, 128:1, 192:1, 224:1, 240:1, 248:1, 252:1, 254:1, 255:1};
            var m = value.split('.');
            var i;

            for (i = 0; i <= 3; i += 1) {
                if (!(valid_values.hasOwnProperty(m[i]))) {
                    return true;
                }
            }
            return false;
        },
        validate: function(attrs) {
            var errors = {};
            var match;
            _.each(this.getAttributes(), _.bind(function(attribute) {
                if (attribute == 'ip_ranges') {
                    if (!_.isEqual(attrs.ip_ranges, [])){
                        _.each(attrs.ip_ranges, _.bind(function(range, index) {
                            if (_.first(range) || _.last(range)) {
                                var rangeErrors = {index: index};
                                var start = _.first(range);
                                var end = _.last(range);
                                if (start && this.validateIP(start)) {
                                    rangeErrors.start = 'Invalid IP range start';
                                }
                                if (end && this.validateIP(end)) {
                                    rangeErrors.end = 'Invalid IP range end';
                                }
                                if (start == '') {
                                    rangeErrors.start = 'Empty IP range start';
                                }
                                if (end == '') {
                                    rangeErrors.end = 'Empty IP range end';
                                }
                                if (start == '' && end == '') {
                                    rangeErrors.start = rangeErrors.end = 'Empty IP range';
                                }
                                if (rangeErrors.start || rangeErrors.end) {
                                    errors.ip_ranges = _.compact(_.union([rangeErrors], errors.ip_ranges));
                                }
                            }
                        }, this));
                    } else {
                        var rangeErrors = {index: 0};
                        var emptyRangeError = 'Please specify at least one IP range';
                        rangeErrors.start = rangeErrors.end = emptyRangeError;
                        errors.ip_ranges = _.compact(_.union([rangeErrors], errors.ip_ranges));
                    }
                } else if (attribute == 'cidr') {
                    var cidrRegexp = /^(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\/([1-9]|[1-2]\d|3[0-2])$/;
                    if (_.isString(attrs.cidr)) {
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
                } else if (attribute == 'vlan_start') {
                    if (!_.isNull(attrs.vlan_start)) {
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
                    }
                } else if (attribute == 'netmask' && this.validateNetmask(attrs.netmask)) {
                    errors.netmask = 'Invalid netmask';
                } else if (attribute == 'gateway' && this.validateIP(attrs.gateway)) {
                    errors.gateway = 'Invalid gateway';
                } else if (attribute == 'amount') {
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
                        errors.amount = 'Number of networks needs more VLAN IDs than available. Check VLAN ID Range field.';
                    }
                }
            }, this));
            return _.isEmpty(errors) ? null : errors;
        }
    });

    models.Networks = Backbone.Collection.extend({
        constructorName: 'Networks',
        model: models.Network,
        preferredOrder: ['public', 'floating', 'management', 'storage', 'fixed'],
        comparator: function(network) {
            return _.indexOf(this.preferredOrder, network.get('name'));
        }
    });

    models.NetworkConfiguration = Backbone.Model.extend({
        constructorName: 'NetworkConfiguration',
        urlRoot: '/api/clusters',
        parse: function(response) {
            response.networks = new models.Networks(response.networks);
            return response;
        },
        toJSON: function() {
            return {
                net_manager: this.get('net_manager'),
                networks: this.get('networks').toJSON()
            };
        },
        isNew: function() {
            return false;
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

    models.RedHatAccount = Backbone.Model.extend({
        constructorName: 'RedHatAccount',
        urlRoot: '/api/redhat/account',
        validate: function(attrs) {
            var errors = [];
            var fields = ['username', 'password'];
            if (attrs.license_type == 'rhn') {
                fields = _.union(fields, ['hostname', 'activation_key']);
            }
            _.each(fields, function(attr) {
                if ($.trim(attrs[attr]) == '') {
                    errors.push(attr);
                }
            });
            return errors.length ? errors : null;
        }
    });

    return models;
});
