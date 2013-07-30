/*
 * Copyright 2013 Mirantis, Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use this file except in compliance with the License. You may obtain
 * a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations
 * under the License.
**/
define(['utils'], function(utils) {
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

    models.NodesStatistics = Backbone.Model.extend({
        constructorName: 'NodesStatistics',
        urlRoot: '/api/nodes/allocation/stats'
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
        parse: function(response) {
            response.volumes = new models.Volumes(response.volumes);
            response.volumes.disk = this;
            return response;
        },
        toJSON: function(options) {
            return _.extend(this.constructor.__super__.toJSON.call(this, options), {volumes: this.get('volumes').toJSON()});
        },
        getUnallocatedSpace: function(options) {
            options = options || {};
            var volumes = options.volumes || this.get('volumes');
            var allocatedSpace = volumes.reduce(function(sum, volume) {return volume.get('name') == options.skip ? sum : sum + volume.get('size');}, 0);
            return this.get('size') - allocatedSpace;
        },
        validate: function(attrs) {
            var error;
            var unallocatedSpace = this.getUnallocatedSpace({volumes: attrs.volumes});
            if (unallocatedSpace < 0) {
                error = 'Volume groups total size exceeds available space of ' + utils.formatNumber(unallocatedSpace * -1) + ' MB';
            }
            return error;
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

    models.Volume = Backbone.Model.extend({
        constructorName: 'Volume',
        urlRoot: '/api/volumes/',
        getMinimalSize: function(minimum) {
            var currentDisk = this.collection.disk;
            var groupAllocatedSpace = currentDisk.collection.reduce(function(sum, disk) {return disk.id == currentDisk.id ? sum : sum + disk.get('volumes').findWhere({name: this.get('name')}).get('size');}, 0, this);
            return minimum - groupAllocatedSpace;
        },
        validate: function(attrs, options) {
            var error;
            var minimumOnDisk = attrs.size ? 65 : 0; // FIXME: revert it
            var min = _.max([minimumOnDisk, this.getMinimalSize(options.minimum)]);
            if (_.isNaN(attrs.size)) {
                error = 'Invalid size';
            } else if (attrs.size < min) {
                error = 'The value is too low. You must allocate at least ' + utils.formatNumber(min) + ' MB';
            }
            return error;
        }
    });

    models.Volumes = Backbone.Collection.extend({
        constructorName: 'Volumes',
        model: models.Volume,
        url: '/api/volumes/'
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
        validateIPrange: function(startIP, endIP) {
            var start = startIP.split('.'), end = endIP.split('.');
            var valid = true;
            _.each(start, function(el, index) {
                if (parseInt(el, 10) > parseInt(end[index], 10)) {
                    valid = false;
                }
            });
            return valid;
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
        validate: function(attrs, options) {
            var errors = {};
            var match;
            _.each(this.getAttributes(), _.bind(function(attribute) {
                if (attribute == 'ip_ranges') {
                    if (_.filter(attrs.ip_ranges, function(range) {return !_.isEqual(range, ['', '']);}).length){
                        _.each(attrs.ip_ranges, _.bind(function(range, index) {
                            if (_.first(range) || _.last(range)) {
                                var rangeErrors = {index: index};
                                var start = _.first(range);
                                var end = _.last(range);
                                if (start == '') {
                                    rangeErrors.start = 'Empty IP range start';
                                } else if (this.validateIP(start)) {
                                    rangeErrors.start = 'Invalid IP range start';
                                }
                                if (end == '') {
                                    rangeErrors.end = 'Empty IP range end';
                                } else if (this.validateIP(end)) {
                                    rangeErrors.end = 'Invalid IP range end';
                                }
                                if (start != '' && end != '' && !this.validateIPrange(start, end)) {
                                    rangeErrors.start = rangeErrors.end = 'Lower IP range bound is greater than upper bound';
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
                    if (!_.isNull(attrs.vlan_start) || (attrs.name == 'fixed' && options.net_manager == 'VlanManager')) {
                        if (_.isNaN(attrs.vlan_start) || !_.isNumber(attrs.vlan_start) || attrs.vlan_start < 1 || attrs.vlan_start > 4094) {
                            errors.vlan_start = 'Invalid VLAN ID';
                        }
                    }
                } else if (attribute == 'netmask' && this.validateNetmask(attrs.netmask)) {
                    errors.netmask = 'Invalid netmask';
                } else if (attribute == 'gateway' && this.validateIP(attrs.gateway)) {
                    errors.gateway = 'Invalid gateway';
                } else if (attribute == 'amount') {
                    if (!attrs.amount || (attrs.amount && (!_.isNumber(attrs.amount) || attrs.amount < 1))) {
                        errors.amount = 'Invalid amount of networks';
                    } else if (attrs.amount && attrs.amount > 4095 - attrs.vlan_start) {
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
            var regex = {
                username: /^[A-z0-9._%+\-@]+$/,
                password: /^[\x00-\x7F]+$/,
                satellite: /^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$/,
                activation_key: /^[A-z0-9*.+\-]+$/
            };
            var fields = ['username', 'password'];
            if (attrs.license_type == 'rhn') {
                fields = _.union(fields, ['satellite', 'activation_key']);
            }
            _.each(fields, function(attr) {
                if (!regex[attr].test($.trim(attrs[attr]))) {
                    errors.push(attr);
                }
            });
            return errors.length ? errors : null;
        }
    });

    models.TestSet = Backbone.Model.extend({
        constructorName: 'TestSet',
        urlRoot: '/ostf/testsets'
    });

    models.TestSets = Backbone.Collection.extend({
        constructorName: 'TestSets',
        model: models.TestSet,
        url: '/ostf/testsets'
    });

    models.Test = Backbone.Model.extend({
        constructorName: 'Test',
        urlRoot: '/ostf/tests'
    });

    models.Tests = Backbone.Collection.extend({
        constructorName: 'Tests',
        model: models.Test,
        url: '/ostf/tests'
    });

    models.TestRun = Backbone.Model.extend({
        constructorName: 'TestRun',
        urlRoot: '/ostf/testruns'
    });

    models.TestRuns = Backbone.Collection.extend({
        constructorName: 'TestRuns',
        model: models.TestRun,
        url: '/ostf/testruns'
    });

    models.OSTFClusterMetadata = Backbone.Model.extend({
        constructorName: 'TestRun',
        urlRoot: '/api/ostf'
    });

    return models;
});
