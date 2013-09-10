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
define(
[
    'utils',
    'models',
    'views/common',
    'views/dialogs',
    'text!templates/cluster/nodes_management_panel.html',
    'text!templates/cluster/assign_roles_panel.html',
    'text!templates/cluster/node_list.html',
    'text!templates/cluster/node_group.html',
    'text!templates/cluster/node.html',
    'text!templates/cluster/node_status.html',
    'text!templates/cluster/edit_node_disks.html',
    'text!templates/cluster/node_disk.html',
    'text!templates/cluster/volume_style.html',
    'text!templates/cluster/edit_node_interfaces.html',
    'text!templates/cluster/node_interface.html'
],
function(utils, models, commonViews, dialogViews, nodesManagementPanelTemplate, assignRolesPanelTemplate, nodeListTemplate, nodeGroupTemplate, nodeTemplate, nodeStatusTemplate, editNodeDisksScreenTemplate, nodeDisksTemplate, volumeStylesTemplate, editNodeInterfacesScreenTemplate, nodeInterfaceTemplate) {
    'use strict';
    var NodesTab, Screen, NodeListScreen, ClusterNodesScreen, AddNodesScreen, NodesManagementPanel, AssignRolesPanel, NodeList, NodeGroup, Node, EditNodeScreen, EditNodeDisksScreen, NodeDisk, EditNodeInterfacesScreen, NodeInterface;

    NodesTab = commonViews.Tab.extend({
        className: 'wrapper',
        screen: null,
        scrollPositions: {},
        hasChanges: function() {
            return this.screen && _.result(this.screen, 'hasChanges');
        },
        changeScreen: function(NewScreenView, screenOptions) {
            var options = _.extend({model: this.model, tab: this, screenOptions: screenOptions || []});
            var newScreen = new NewScreenView(options);
            var oldScreen = this.screen;
            if (oldScreen) {
                if (oldScreen.keepScrollPosition) {
                    this.scrollPositions[oldScreen.constructorName] = $(window).scrollTop();
                }
                oldScreen.$el.fadeOut('fast', _.bind(function() {
                    oldScreen.tearDown();
                    newScreen.render();
                    newScreen.$el.hide().fadeIn('fast');
                    this.$el.html(newScreen.el);
                    if (newScreen.keepScrollPosition && this.scrollPositions[newScreen.constructorName]) {
                        $(window).scrollTop(this.scrollPositions[newScreen.constructorName]);
                    }
                }, this));
            } else {
                this.$el.html(newScreen.render().el);
            }
            this.screen = newScreen;
            this.registerSubView(this.screen);
        },
        initialize: function(options) {
            _.defaults(this, options);
            this.revertChanges = _.bind(function() {
                return this.screen && this.screen.revertChanges();
            }, this);
        },
        routeScreen: function(options) {
            var screens = {
                'list': ClusterNodesScreen,
                'add': AddNodesScreen,
                'disks': EditNodeDisksScreen,
                'interfaces': EditNodeInterfacesScreen
            };
            this.changeScreen(screens[options[0]] || screens.list, options.slice(1));
        },
        render: function() {
            this.routeScreen(this.tabOptions);
            return this;
        }
    });

    Screen = Backbone.View.extend({
        constructorName: 'Screen',
        keepScrollPosition: false,
        goToNodeList: function() {
            app.navigate('#cluster/' + this.model.id + '/nodes', {trigger: true});
        }
    });

    NodeListScreen = Screen.extend({
        constructorName: 'NodeListScreen',
        updateInterval: 20000,
        scheduleUpdate: function() {
            this.registerDeferred($.timeout(this.updateInterval).done(_.bind(this.update, this)));
        },
        update: function() {
            this.nodes.fetch().always(_.bind(this.scheduleUpdate, this));
        },
        calculateBatchActionsButtonsState: function() {
            this.$('.batch-action-btn').prop('disabled', !this.$('.node.checked').length);
        },
        render: function() {
            this.tearDownRegisteredSubViews();
            this.$el.html('');
            var managementPanel = new NodesManagementPanel({screen: this});
            this.registerSubView(managementPanel);
            this.$el.append(managementPanel.render().el);
            this.list = new NodeList({nodes: this.nodes, screen: this});
            this.registerSubView(this.list);
            this.$el.append(this.list.render().el);
            return this;
        }
    });

    ClusterNodesScreen = NodeListScreen.extend({
        className: 'cluster-nodes-screen',
        constructorName: 'ClusterNodesScreen',
        initialize: function(options) {
            _.defaults(this, options);
            this.constructor.__super__.initialize.apply(this, arguments);
            this.nodes = this.model.get('nodes');
            this.nodes.cluster = this.model;
            var clusterId = this.model.id;
            this.nodes.fetch = function(options) {
                return this.constructor.__super__.fetch.call(this, _.extend({data: {cluster_id: clusterId}}, options));
            };
            this.nodes.fetch().done(_.bind(this.render, this));
            this.nodes.on('resize change:pending_roles', this.render, this); // FIXME: should it be moved to NodeList view?
            this.model.on('change:mode change:status', this.render, this); // FIXME: should it be moved to NodeList view?
            this.model.get('tasks').each(this.bindTaskEvents, this);
            this.model.get('tasks').on('add', this.onNewTask, this);
            this.scheduleUpdate();
        },
        bindTaskEvents: function(task) {
            return (task.get('name') == 'deploy' || task.get('name') == 'verify_networks') ? task.on('change:status', this.render, this) : null;
        },
        onNewTask: function(task) {
            return this.bindTaskEvents(task) && this.render();
        }
    });

    AddNodesScreen = NodeListScreen.extend({
        className: 'add-nodes-screen',
        constructorName: 'AddNodesScreen',
        events: {
            'click .btn-go-to-cluster': 'goToNodeList'
        },
        initialize: function(options) {
            _.defaults(this, options);
            this.constructor.__super__.initialize.apply(this, arguments);
            this.nodes = new models.Nodes();
            this.nodes.fetch = function(options) {
                return this.constructor.__super__.fetch.call(this, _.extend({data: {cluster_id: ''}}, options));
            };
            this.nodes.fetch().done(_.bind(this.render, this));
            this.nodes.on('resize', this.render, this); // FIXME: should it be moved to NodeList view?
            this.scheduleUpdate();
        }
    });

    NodesManagementPanel = Backbone.View.extend({
        className: 'nodes-management-panel',
        template: _.template(nodesManagementPanelTemplate),
        events: {
            'change select[name=grouping]' : 'groupNodes',
            'click .btn-cluster-actions': 'changeClusterMode',
            'click .btn-assign-roles:not(:disabled)' : 'showAssignRolesPanel',
            'click .btn-delete-nodes:not(:disabled)' : 'showDeleteNodesDialog',
            'click .btn-configure-disks:not(:disabled)' : 'goToConfigureDisksScreen',
            'click .btn-configure-interfaces:not(:disabled)' : 'goToConfigureInterfacesScreen'
        },
        initialize: function(options) {
            _.defaults(this, options);
            this.cluster = this.screen.nodes.cluster;
        },
        groupNodes: function(e) {
            var grouping = this.$(e.currentTarget).val();
            this.cluster.save({grouping: grouping}, {patch: true, wait: true});
            this.screen.list.groupNodes(grouping);
        },
        chosenNodes: function() {
            var chosenNodesIds = this.screen.$('.node-checkbox input:checked').map(function() {return parseInt($(this).val(), 10);}).get();
            return this.screen.nodes.filter(function(node) {return _.contains(chosenNodesIds, node.id);});
        },
        changeClusterMode: function() {
            var dialog = new dialogViews.ChangeClusterModeDialog({model: this.cluster});
            this.registerSubView(dialog);
            dialog.render();
        },
        showAssignRolesPanel: function() {
            this.$('.cluster-toolbar').hide();
            var nodes = new models.Nodes(this.chosenNodes());
            nodes.cluster = this.cluster;
            var assignRolesPanel = new AssignRolesPanel({nodes: nodes});
            this.registerSubView(assignRolesPanel);
            this.$('.assign-roles-panel').html(assignRolesPanel.render().el);
        },
        showDeleteNodesDialog: function() {
            var nodes = new models.Nodes(this.chosenNodes());
            nodes.cluster = this.cluster;
            var dialog = new dialogViews.DeleteNodesDialog({nodes: nodes});
            app.page.tab.registerSubView(dialog);
            dialog.render();
        },
        goToConfigureDisksScreen: function() {
        },
        goToConfigureInterfacesScreen: function() {
        },
        render: function() {
            this.tearDownRegisteredSubViews();
            this.$el.html(this.template({nodes: this.screen.nodes}));
            return this;
        }
    });

    AssignRolesPanel = Backbone.View.extend({
        template: _.template(assignRolesPanelTemplate),
        className: 'roles-panel',
        events: {
            'click .btn-close' : 'hidePanel',
            'change input[type=checkbox]' : 'handleChanges',
            'click .btn-assign:not(:disabled)' : 'assignRoles'
        },
        hidePanel: function() {
            this.$el.hide();
            app.page.tab.screen.$('.cluster-toolbar').show();
        },
        handleChanges: function(e) {
            this.checkForConflicts();
            this.calculateInputState(e);
            this.calculateAssignButtonState();
        },
        checkForConflicts: function(e) {
            this.$('input').prop('disabled', false);
            this.$('.role-conflict').text('');
            // check uncompatible roles
            var selectedRolesInputs = _.filter(this.$('input'), function(input) {return $(input).prop('indeterminate') || $(input).prop('checked');});
            var selectedRoles = selectedRolesInputs.map(function(input) {return $(input).val();});
            _.each(this.getListOfUncompatibleRoles(selectedRoles), function(role) {
                this.$('input[value=' + role + ']').prop('disabled', true);
                this.$('.role-conflict.' + role).text('This role can not be assigned together with selected roles.');
            }, this);
            // non-ha deployment mode restriction: environment can not have more than one controller node
            if (this.nodes.length > 1 && this.cluster.get('mode') != 'ha_compact') {
                this.$('input[value=controller]').prop('disabled', true);
                this.$('.role-conflict.controller').text('This role can not be assigned to more than one node in Multinode deployment mode.');
            }
        },
        getListOfUncompatibleRoles: function(roles) {
            var forbiddenRoles = [];
            var release = this.cluster.get('release');
            _.each(roles, function(role) {
                forbiddenRoles = _.union(forbiddenRoles, release.get('roles_metadata')[role].conflicts);
            });
            return _.uniq(forbiddenRoles);
        },
        calculateInputState: function(e) {
            var input = this.$(e.currentTarget);
            var role = input.val();
            if (!input.is(':checked')) {
                // count deployed nodes with this role
                var deployedNodes = this.nodes.filter(function(node) {return !node.get('pending_addition') && _.contains(node.get('roles'), role);});
                this.inputState(role, deployedNodes);
            }
        },
        inputState: function(role, nodes) {
            var prop = nodes.length ? nodes.length == this.nodes.length ? 'checked' : 'indeterminate' : '';
            this.$('input[value=' + role + ']').prop(prop, true);
            return prop;
        },
        calculateAssignButtonState: function() {
            var inputStates = {};
            _.each(this.roles, function(role) {
                var input = this.$('input[value=' + role + ']');
                inputStates[role] = input.is(':checked') ? 'checked' : input.prop('indeterminate') ? 'indeterminate' : '';
            }, this);
            this.$('.btn-assign').prop('disabled', _.isEqual(this.initialData, inputStates));
        },
        assignRoles: function() {
            this.$('.btn-assign').prop('disabled', true);
            // set roles
            _.each(this.$('input'), function(input) {
                var role = $(input).val();
                if ($(input).is(':checked')) { // assign role to all nodes
                    this.nodes.each(function(node) {node.set({pending_roles: _.uniq(_.union(node.get('pending_roles'), role))});});
                } else if (!$(input).prop('indeterminate')) { // remove role from all nodes
                    this.nodes.each(function(node) {node.set({pending_roles: _.difference(node.get('pending_roles'), role)});});
                }
            }, this);
            // set pending_addition flag
            if (!this.nodes.cluster) {
                this.nodes.each(function(node) {node.set({
                    cluster_id: app.page.tab.model.id,
                    pending_addition: true
                });});
            }
            this.nodes.toJSON = function(options) {
                return this.map(function(node) {
                    return _.pick(node.attributes, 'id', 'cluster_id', 'pending_roles', 'pending_addition');
                });
            };
            this.nodes.sync('update', this.nodes)
                .done(_.bind(function() {
                    this.cluster.fetch();
                    app.page.tab.screen.nodes.fetch();
                    app.navbar.refresh();
                    app.page.removeFinishedTasks();
                }, this))
                .fail(_.bind(function() {
                    this.$('.btn-assign').prop('disabled', false);
                    utils.showErrorDialog({title: 'Unable to assign roles'});
                }, this));
        },
        initialize: function(options) {
            _.defaults(this, options);
            this.cluster = app.page.tab.screen.model;
            this.roles = this.cluster.availableRoles();
        },
        setInitialData: function() {
            this.initialData = {};
            _.each(this.roles, function(role) {
                var nodes = this.nodes.filter(function(node) {return _.contains(node.get('pending_roles'), role);});
                this.initialData[role] = this.inputState(role, nodes);
            }, this);
        },
        render: function() {
            this.$el.html(this.template({
                nodes: this.nodes,
                roles: this.roles,
                rolesData: this.cluster.get('release').get('roles_metadata')
            }));
            this.setInitialData();
            this.checkForConflicts();
            return this;
        }
    });

    NodeList = Backbone.View.extend({
        className: 'node-list',
        template: _.template(nodeListTemplate),
        events: {
            'change input[name=select-nodes-common]' : 'selectAllNodes'
        },
        selectAllNodes: function(e) {
            this.$('input[name=select-node-group]').prop('checked', this.$(e.currentTarget).is(':checked')).trigger('change');
            this.screen.calculateBatchActionsButtonsState();
        },
        calculateSelectAllTumblerState: function() {
            this.$('input[name=select-nodes-common]').prop('checked', this.$('.node-checkbox input:checked').length == this.$('.node-box:not(.node-offline)').length);
        },
        groupNodes: function(attribute) {
            if (_.isUndefined(attribute)) {
                attribute = this.nodes.cluster ? this.nodes.cluster.get('grouping') : 'hardware';
            }
            if (attribute == 'roles') {
                this.nodeGroups = this.nodes.groupBy(function(node) {return _.union(node.get('roles'), node.get('pending_roles')).join(' + ');});
            } else if (attribute == 'hardware') {
                this.nodeGroups = this.nodes.groupBy(function(node) {return 'HDD: ' + utils.showDiskSize(node.resource('hdd')) + ' RAM: ' + utils.showMemorySize(node.resource('ram'));});
            } else {
                this.nodeGroups = this.nodes.groupBy(function(node) {return _.union(node.get('roles'), node.get('pending_roles')).join(' + ') + ' HDD: ' + utils.showDiskSize(node.resource('hdd')) + ' RAM: ' + utils.showMemorySize(node.resource('ram'));});
            }
            this.renderNodeGroups();
        },
        initialize: function(options) {
            _.defaults(this, options);
        },
        renderNodeGroups: function() {
            this.$('.nodes').html('');
            _.each(_.keys(this.nodeGroups), function(groupLabel) {
                var nodeGroupView = new NodeGroup({
                    groupLabel: groupLabel,
                    nodes: new models.Nodes(this.nodeGroups[groupLabel]),
                    list: this
                });
                this.registerSubView(nodeGroupView);
                this.$('.nodes').append(nodeGroupView.render().el);
            }, this);
        },
        render: function() {
            this.tearDownRegisteredSubViews();
            this.$el.html(this.template({nodes: this.nodes}));
            this.groupNodes();
            return this;
        }
    });

    NodeGroup = Backbone.View.extend({
        className: 'node-group',
        template: _.template(nodeGroupTemplate),
        events: {
            'change input[name=select-node-group]' : 'selectAllNodes'
        },
        selectAllNodes: function(e) {
            var checked = this.$(e.currentTarget).is(':checked');
            _.each(this.subViews, function(nodeView) {
                if (nodeView.node.get('online')) {
                    nodeView.checked = checked;
                    nodeView.$el.toggleClass('checked', checked);
                    nodeView.render();
                }
            });
            this.list.calculateSelectAllTumblerState();
            this.list.screen.calculateBatchActionsButtonsState();
        },
        calculateSelectAllTumblerState: function() {
            this.$('input[name=select-node-group]').prop('checked', this.$('.node-checkbox input:checked').length == this.$('.node-box:not(.node-offline)').length);
            this.list.calculateSelectAllTumblerState();
        },
        initialize: function(options) {
            _.defaults(this, options);
        },
        renderNode: function(node) {
            var nodeView = new Node({
                node: node,
                renameable: true,
                group: this
            });
            this.registerSubView(nodeView);
            this.$('.nodes-group').append(nodeView.render().el);
        },
        render: function() {
            this.tearDownRegisteredSubViews();
            this.$el.html(this.template({
                groupLabel: this.groupLabel,
                nodes: this.nodes
            }));
            this.nodes.each(this.renderNode, this);
            return this;
        }
    });

    Node = Backbone.View.extend({
        className: 'node',
        template: _.template(nodeTemplate),
        nodeStatusTemplate: _.template(nodeStatusTemplate),
        templateHelpers: _.pick(utils, 'showDiskSize', 'showMemorySize'),
        events: {
            'change .node-checkbox input': 'selectNode',
            'click .node-renameable': 'startNodeRenaming',
            'keydown .name input': 'onNodeNameInputKeydown',
            'click .node-hardware': 'showNodeDetails',
            'click .roles li': 'showAssignRolesPanel',
            'click .btn-discard-role-changes': 'discardRoleChanges',
            'click .btn-discard-addition': 'discardAddition',
            'click .btn-discard-deletion': 'discardDeletion'
        },
        selectNode: function() {
            this.$el.toggleClass('checked');
            this.checked = !this.checked;
            this.group.calculateSelectAllTumblerState();
            this.group.list.screen.calculateBatchActionsButtonsState();
        },
        startNodeRenaming: function() {
            if (!this.renameable || this.renaming) {return;}
            $('html').off(this.eventNamespace);
            $('html').on(this.eventNamespace, _.after(2, _.bind(function(e) {
                if (!$(e.target).closest(this.$('.name input')).length) {
                    this.endNodeRenaming();
                }
            }, this)));
            this.renaming = true;
            this.render();
            this.$('.name input').focus();
        },
        endNodeRenaming: function() {
            $('html').off(this.eventNamespace);
            this.renaming = false;
            this.render();
        },
        applyNewNodeName: function() {
            var name = $.trim(this.$('.name input').val());
            if (name && name != this.node.get('name')) {
                this.$('.name input').attr('disabled', true);
                this.node.save({name: name}, {patch: true, wait: true}).always(_.bind(this.endNodeRenaming, this));
            } else {
                this.endNodeRenaming();
            }
        },
        onNodeNameInputKeydown: function(e) {
            if (e.which == 13) {
                this.applyNewNodeName();
            } else if (e.which == 27) {
                this.endNodeRenaming();
            }
        },
        showNodeDetails: function() {
            var dialog = new dialogViews.ShowNodeInfoDialog({node: this.node});
            app.page.tab.registerSubView(dialog);
            dialog.render();
        },
        showAssignRolesPanel: function() {
            var assignRolesPanel = new AssignRolesPanel({nodes: new models.Nodes(this.node)});
            this.registerSubView(assignRolesPanel);
            this.$('.assign-roles-panel').html(assignRolesPanel.render().el);
        },
        updateNode: function(data) {
            var screen = app.page.tab.screen;
            this.node
                .save(data, {patch: true, wait: true})
                .done(function() {screen.nodes.fetch();})
                .fail(function() {utils.showErrorDialog({title: "Can't discard node changes"});});
        },
        discardRoleChanges: function() {
            var data = {pending_roles: []};
            if (this.node.get('pending_addition')) {
                data.cluster = null;
                data.pending_addition = false;
            }
            this.updateNode(data);
        },
        discardAddition: function() {
            this.updateNode({
                cluster: null,
                pending_addition: false,
                pending_roles: []
            });
        },
        discardDeletion: function() {
            this.updateNode({pending_deletion: false});
        },
        updateProgress: function() {
            if (this.node.get('status') == 'provisioning' || this.node.get('status') == 'deploying') {
                var progress = this.node.get('progress') || 0;
                this.$('.bar').css('width', (progress > 3 ? progress : 3) + '%');
            }
        },
        updateStatus: function() {
            this.$('.node-status').html(this.nodeStatusTemplate({
                node: this.node,
                logsLink: this.getLogsLink()
            }));
            this.$('.node-box').toggleClass('node-offline', !this.node.get('online'));
            this.updateProgress();
        },
        getLogsLink: function() {
            var status = this.node.get('status');
            var error = this.node.get('error_type');
            var options = {type: 'remote', node: this.node.id};
            if (status == 'discover') {
                options.source = 'bootstrap/messages';
            } else if (status == 'provisioning' || status == 'provisioned' || (status == 'error' && error == 'provision')) {
                options.source = 'install/anaconda';
            } else if (status == 'deploying' || status == 'ready' || (status == 'error' && error == 'deploy')) {
                options.source = 'install/puppet';
            }
            return '#cluster/' + app.page.model.id + '/logs/' + utils.serializeTabOptions(options);
        },
        beforeTearDown: function() {
            $('html').off(this.eventNamespace);
        },
        initialize: function(options) {
            _.defaults(this, options);
            this.renaming = false;
            this.checked = false;
            this.eventNamespace = 'click.editnodename' + this.node.id;
            this.node.on('change:name change:pending_addition change:pending_deletion change:online change:pending_roles', this.render, this);
            this.node.on('change:status change:online', this.updateStatus, this);
            this.node.on('change:progress', this.updateProgress, this);
        },
        render: function() {
            this.tearDownRegisteredSubViews();
            this.$el.html(this.template(_.extend({
                node: this.node,
                renaming: this.renaming,
                renameable: this.renameable,
                checked: this.checked
            }, this.templateHelpers)));
            this.updateStatus();
            return this;
        }
    });

    EditNodeScreen = Screen.extend({
        constructorName: 'EditNodeScreen',
        keepScrollPosition: true,
        disableControls: function(disable) {
            this.$('.btn, input').attr('disabled', disable || this.isLocked());
        },
        returnToNodeList: function() {
            if (this.hasChanges()) {
                app.page.tab.discardSettingsChanges({cb: _.bind(this.goToNodeList, this)});
            } else {
                this.goToNodeList();
            }
        },
        isLocked: function() {
            return !!this.model.task('deploy', 'running');
        }
    });

    EditNodeDisksScreen = EditNodeScreen.extend({
        className: 'edit-node-disks-screen',
        constructorName: 'EditNodeDisksScreen',
        template: _.template(editNodeDisksScreenTemplate),
        events: {
            'click .btn-defaults': 'loadDefaults',
            'click .btn-revert-changes': 'revertChanges',
            'click .btn-apply:not(:disabled)': 'applyChanges',
            'click .btn-return:not(:disabled)': 'returnToNodeList'
        },
        hasChanges: function() {
            return !_.isEqual(this.disks.toJSON(), this.initialData);
        },
        hasValidationErrors: function() {
            var result = false;
            this.disks.each(function(disk) {result = result || _.some(disk.get('volumes').models, 'validationError');}, this);
            return result;
        },
        isLocked: function() {
            return !(this.node.get('pending_addition') || (this.node.get('status') == 'error' && this.node.get('error_type') == 'provision')) || this.constructor.__super__.isLocked.apply(this);
        },
        checkForChanges: function() {
            var hasChanges = this.hasChanges();
            var hasValidationErrors = this.hasValidationErrors();
            this.$('.btn-apply').attr('disabled', !hasChanges || hasValidationErrors);
            this.$('.btn-revert-changes').attr('disabled', !hasChanges && !hasValidationErrors);
            this.$('.btn-defaults').attr('disabled', false);
        },
        loadDefaults: function() {
            this.disableControls(true);
            this.disks.fetch({url: _.result(this.node, 'url') + '/disks/defaults/'})
                .fail(_.bind(function() {
                    utils.showErrorDialog({title: 'Node disks configuration'});
                }, this));
        },
        revertChanges: function() {
            this.disks.reset(_.cloneDeep(this.initialData), {parse: true});
        },
        applyChanges: function() {
            if (this.hasValidationErrors()) {
                return (new $.Deferred()).reject();
            }
            this.disableControls(true);
            return Backbone.sync('update', this.disks, {url: _.result(this.node, 'url') + '/disks'})
                .done(_.bind(function() {
                    this.model.fetch();
                    this.initialData = _.cloneDeep(this.disks.toJSON());
                    this.render();
                }, this))
                .fail(_.bind(function() {
                    this.checkForChanges();
                    utils.showErrorDialog({title: 'Node disks configuration'});
                }, this));
        },
        mapVolumesColors: function() {
            this.volumesColors = {};
            var colors = [
                ['#23a85e', '#1d8a4d'],
                ['#3582ce', '#2b6ba9'],
                ['#eea616', '#c38812'],
                ['#1cbbb4', '#189f99'],
                ['#9e0b0f', '#870a0d'],
                ['#8f50ca', '#7a44ac'],
                ['#1fa0e3', '#1b88c1'],
                ['#85c329', '#71a623'],
                ['#7d4900', '#6b3e00']
            ];
            this.volumes.each(function(volume, index) {
                this.volumesColors[volume.get('name')] = colors[index];
            }, this);
        },
        initialize: function(options) {
            _.defaults(this, options);
            this.node = this.model.get('nodes').get(this.screenOptions[0]);
            if (this.node) {
                this.model.on('change:status', this.revertChanges, this);
                this.volumes = new models.Volumes([], {url: _.result(this.node, 'url') + '/volumes'});
                this.disks = new models.Disks([], {url: _.result(this.node, 'url') + '/disks'});
                this.loading = $.when(this.node.fetch(), this.volumes.fetch(), this.disks.fetch())
                    .done(_.bind(function() {
                        this.initialData = _.cloneDeep(this.disks.toJSON());
                        this.mapVolumesColors();
                        this.render();
                        this.disks.on('sync', this.render, this);
                        this.disks.on('reset', this.render, this);
                        this.disks.on('error', this.checkForChanges, this);
                    }, this))
                    .fail(_.bind(this.goToNodeList, this));
            } else {
                this.goToNodeList();
            }
        },
        renderDisks: function() {
            this.tearDownRegisteredSubViews();
            this.$('.node-disks').html('');
            this.disks.each(function(disk) {
                var nodeDisk = new NodeDisk({
                    disk: disk,
                    diskMetaData: _.find(this.node.get('meta').disks, {disk: disk.id}),
                    screen: this
                });
                this.registerSubView(nodeDisk);
                this.$('.node-disks').append(nodeDisk.render().el);
            }, this);
        },
        render: function() {
            this.$el.html(this.template({
                node: this.node,
                locked: this.isLocked()
            }));
            if (this.loading && this.loading.state() != 'pending') {
                this.renderDisks();
                this.checkForChanges();
            }
            return this;
        }
    });

    NodeDisk = Backbone.View.extend({
        template: _.template(nodeDisksTemplate),
        volumeStylesTemplate: _.template(volumeStylesTemplate),
        templateHelpers: {
            sortEntryProperties: function(entry) {
                var properties = _.keys(entry);
                if (_.has(entry, 'name')) {
                    properties = ['name'].concat(_.keys(_.omit(entry, ['name'])));
                }
                return properties;
            },
            showDiskSize: utils.showDiskSize
        },
        events: {
            'click .toggle-volume': 'toggleEditDiskForm',
            'click .close-btn': 'deleteVolume',
            'keyup input': 'updateDisks',
            'click .use-all-allowed': 'useAllAllowedSpace'
        },
        toggleEditDiskForm: function(e) {
            if (this.screen.isLocked()) {return;}
            this.$('.disk-form').collapse('toggle');
            this.checkForGroupsDeletionAvailability();
        },
        getVolumeMinimum: function(name) {
            return this.screen.volumes.findWhere({name: name}).get('min_size');
        },
        checkForGroupsDeletionAvailability: function() {
            this.disk.get('volumes').each(function(volume) {
                var name = volume.get('name');
                this.$('.disk-visual .' + name + ' .close-btn').toggle(volume.getMinimalSize(this.getVolumeMinimum(name)) <= 0 && this.$('.disk-form').hasClass('in'));
            }, this);
        },
        validateVolume: function (volume) {
            var name = volume.get('name');
            volume.set({size: Number((this.$('input[name=' + name + ']').val()).replace(/,/g, ''))}, {validate: true, minimum: this.getVolumeMinimum(name)});
        },
        updateDisk: function() {
            this.$('.disk-visual').removeClass('invalid');
            this.$('input').removeClass('error').parents('.volume-group').next().text('');
            this.$('.volume-group-error-message.common').text('');
            this.disk.get('volumes').each(this.validateVolume, this); // volumes validation (minimum)
            this.disk.set({volumes: this.disk.get('volumes')}, {validate: true}); // disk validation (maximum)
            this.renderVisualGraph();
            this.checkForGroupsDeletionAvailability();
        },
        updateDisks: function(e) {
            this.updateDisk();
            _.invoke(_.omit(this.screen.subViews, this.cid), 'updateDisk', this);
            this.screen.checkForChanges();
        },
        deleteVolume: function(e) {
            this.$('input[name=' + this.$(e.currentTarget).parents('.volume-group').data('volume') + ']').val(0).trigger('keyup');
        },
        useAllAllowedSpace: function(e) {
            var volumeName = this.$(e.currentTarget).parents('.volume-group').data('volume');
            this.$('input[name=' + volumeName + ']').val(_.max([0, this.disk.getUnallocatedSpace({skip: volumeName})])).trigger('keyup');
        },
        initialize: function(options) {
            _.defaults(this, options);
            this.disk.on('invalid', function(model, error) {
                this.$('.disk-visual').addClass('invalid');
                this.$('input').addClass('error');
                this.$('.volume-group-error-message.common').text(error);
            }, this);
            this.disk.get('volumes').each(function(volume) {
                volume.on('invalid', function(model, error) {
                    this.$('.disk-visual').addClass('invalid');
                    this.$('input[name=' + volume.get('name') + ']').addClass('error').parents('.volume-group').next().text(error);
                }, this);
            }, this);
        },
        renderVolume: function(name, width, size) {
            this.$('.disk-visual .' + name)
                .toggleClass('hidden-titles', width < 6)
                .css('width', width + '%')
                .find('.volume-group-size').text(utils.showDiskSize(size, 2));
        },
        renderVisualGraph: function() {
            if (!this.disk.get('volumes').some('validationError') && !this.disk.validationError) {
                var unallocatedWidth = 100;
                this.disk.get('volumes').each(function(volume) {
                    var width = this.disk.get('size') ? utils.floor(volume.get('size') / this.disk.get('size') * 100, 2) : 0;
                    unallocatedWidth -= width;
                    this.renderVolume(volume.get('name'), width, volume.get('size'));
                }, this);
                this.renderVolume('unallocated', unallocatedWidth, this.disk.getUnallocatedSpace());
            }
        },
        applyColors: function() {
            this.disk.get('volumes').each(function(volume) {
                var name = volume.get('name');
                var colors = this.screen.volumesColors[name];
                this.$('.disk-visual .' + name + ', .volume-group-box-flag.' + name).attr('style', this.volumeStylesTemplate({startColor: _.first(colors), endColor: _.last(colors)}));
            }, this);
        },
        render: function() {
            this.$el.html(this.template(_.extend({
                diskMetaData: this.diskMetaData,
                disk: this.disk,
                volumes: this.screen.volumes
            }, this.templateHelpers)));
            this.$('.disk-form').collapse({toggle: false});
            this.applyColors();
            this.renderVisualGraph();
            this.$('input').autoNumeric('init', {mDec: 0});
            return this;
        }
    });

    EditNodeInterfacesScreen = EditNodeScreen.extend({
        className: 'edit-node-networks-screen',
        constructorName: 'EditNodeInterfacesScreen',
        template: _.template(editNodeInterfacesScreenTemplate),
        events: {
            'click .btn-defaults': 'loadDefaults',
            'click .btn-revert-changes': 'revertChanges',
            'click .btn-apply:not(:disabled)': 'applyChanges',
            'click .btn-return:not(:disabled)': 'returnToNodeList'
        },
        hasChanges: function() {
            return !_.isEqual(this.interfaces.toJSON(), this.initialData);
        },
        isLocked: function() {
            return !(this.node.get('pending_addition') || this.model.get('status') == 'error') || this.constructor.__super__.isLocked.apply(this);
        },
        checkForChanges: function() {
            this.$('.btn-apply, .btn-revert-changes').attr('disabled', this.isLocked() || !this.hasChanges());
        },
        loadDefaults: function() {
            this.disableControls(true);
            this.interfaces.fetch({url: _.result(this.node, 'url') + '/interfaces/default_assignment', reset: true})
                .done(_.bind(function() {
                    this.disableControls(false);
                    this.checkForChanges();
                }, this))
                .fail(_.bind(function() {
                    this.disableControls(false);
                    utils.showErrorDialog({title: 'Unable to load default settings'});
                }, this));
        },
        revertChanges: function() {
            this.interfaces.reset(_.cloneDeep(this.initialData), {parse: true});
        },
        applyChanges: function() {
            this.disableControls(true);
            var configuration = new models.NodeInterfaceConfiguration({id: this.node.id, interfaces: this.interfaces});
            return Backbone.sync('update', new models.NodeInterfaceConfigurations(configuration))
                .done(_.bind(function() {
                    this.initialData = this.interfaces.toJSON();
                }, this))
                .fail(_.bind(function() {
                    var dialog = new dialogViews.Dialog();
                    app.page.registerSubView(dialog);
                    dialog.displayInfoMessage({error: true, title: 'Node network interfaces configuration error'});
                }, this))
                .always(_.bind(function() {
                    this.disableControls(false);
                    this.checkForChanges();
                }, this));
        },
        initialize: function(options) {
            _.defaults(this, options);
            this.node = this.model.get('nodes').get(this.screenOptions[0]);
            if (this.node) {
                this.model.on('change:status', function() {
                    this.revertChanges();
                    this.render();
                }, this);
                var networkConfiguration = new models.NetworkConfiguration();
                this.interfaces = new models.Interfaces();
                this.loading = $.when(
                   this.interfaces.fetch({url: _.result(this.node, 'url') + '/interfaces', reset: true}),
                   networkConfiguration.fetch({url: _.result(this.model, 'url') + '/network_configuration'})
                ).done(_.bind(function() {
                    // FIXME(vk): modifying models prototypes to use vlan data from NetworkConfiguration
                    // this mean that these models cannot be used safely in places other than this view
                    // helper function for template to get vlan_start NetworkConfiguration
                    models.InterfaceNetwork.prototype.vlanStart = function() {
                        return networkConfiguration.get('networks').findWhere({name: this.get('name')}).get('vlan_start');
                    };
                    models.InterfaceNetwork.prototype.amount = function() {
                        return networkConfiguration.get('networks').findWhere({name: this.get('name')}).get('amount');
                    };
                    this.initialData = this.interfaces.toJSON();
                    this.interfaces.on('reset', this.renderInterfaces, this);
                    this.interfaces.on('reset', this.checkForChanges, this);
                    this.checkForChanges();
                    this.renderInterfaces();
                }, this))
                .fail(_.bind(this.goToNodeList, this));
            } else {
                this.goToNodeList();
            }
        },
        renderInterfaces: function() {
            this.tearDownRegisteredSubViews();
            this.$('.node-networks').html('');
            this.interfaces.each(_.bind(function(ifc) {
                var nodeInterface = new NodeInterface({model: ifc, screen: this});
                this.registerSubView(nodeInterface);
                this.$('.node-networks').append(nodeInterface.render().el);
            }, this));
        },
        render: function() {
            this.$el.html(this.template({
                node: this.node,
                locked: this.isLocked()
            }));
            if (this.loading && this.loading.state() != 'pending') {
                this.renderInterfaces();
            }
            return this;
        }
    });

    NodeInterface = Backbone.View.extend({
        template: _.template(nodeInterfaceTemplate),
        templateHelpers: _.pick(utils, 'showBandwidth'),
        events: {
            'sortremove .logical-network-box': 'dragStart',
            'sortreceive .logical-network-box': 'dragStop',
            'sortstop .logical-network-box': 'dragStop'
        },
        dragStart: function(event, ui) {
            var networkNames = $(ui.item).find('.logical-network-item').map(function(index, el) {return $(el).data('name');}).get();
            var networks = this.model.get('assigned_networks').filter(function(network) {return _.contains(networkNames, network.get('name'));});
            this.model.get('assigned_networks').remove(networks);
            this.screen.draggedNetworks = networks;
        },
        dragStop: function(event, ui) {
            var networks = this.screen.draggedNetworks;
            if (event.type == 'sortreceive') {
                this.model.get('assigned_networks').add(networks);
            }
            this.render();
            this.screen.draggedNetworks = null;
        },
        checkIfEmpty: function() {
            this.$('.network-help-message').toggle(!this.model.get('assigned_networks').length && !this.screen.isLocked());
        },
        initialize: function(options) {
            _.defaults(this, options);
            this.model.get('assigned_networks').on('add remove', this.checkIfEmpty, this);
            this.model.get('assigned_networks').on('add remove', this.screen.checkForChanges, this.screen);
        },
        render: function() {
            this.$el.html(this.template(_.extend({ifc: this.model}, this.templateHelpers)));
            this.checkIfEmpty();
            this.$('.logical-network-box').sortable({
                connectWith: '.logical-network-box',
                items: '.logical-network-group',
                containment: this.screen.$('.node-networks'),
                disabled: this.screen.isLocked()
            }).disableSelection();
            return this;
        }
    });

    return NodesTab;
});
