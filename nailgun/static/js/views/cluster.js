define(
[
    'models',
    'views/dialogs',
    'text!templates/cluster/page.html',
    'text!templates/cluster/deployment_result.html',
    'text!templates/cluster/deployment_control.html',
    'text!templates/cluster/nodes_tab_summary.html',
    'text!templates/cluster/edit_nodes_screen.html',
    'text!templates/cluster/node_list.html',
    'text!templates/cluster/node.html',
    'text!templates/cluster/network_tab.html',
    'text!templates/cluster/network_tab_view.html',
    'text!templates/cluster/verify_network_control.html',
    'text!templates/cluster/settings_tab.html',
    'text!templates/cluster/settings_group.html',
    'text!templates/cluster/actions_tab.html',
    'text!templates/cluster/logs_tab.html'
],
function(models, dialogViews, clusterPageTemplate, deploymentResultTemplate, deploymentControlTemplate, nodesTabSummaryTemplate, editNodesScreenTemplate, nodeListTemplate, nodeTemplate, networkTabTemplate, networkTabViewModeTemplate, networkTabVerificationTemplate, settingsTabTemplate, settingsGroupTemplate, actionsTabTemplate, logsTabTemplate) {
    'use strict';

    var views = {};

    views.ClusterPage = Backbone.View.extend({
        updateInterval: 5000,
        template: _.template(clusterPageTemplate),
        events: {
            'click .task-result .close': 'dismissTaskResult',
            'click .deploy-btn': 'displayChanges'
        },
        dismissTaskResult: function() {
            this.$('.task-result').remove();
            this.model.task('deploy').destroy();
        },
        displayChanges: function() {
            (new dialogViews.DisplayChangesDialog({model: this.model})).render();
        },
        deployCluster: function() {
            var task = new models.Task();
            task.save({}, {
                type: 'PUT',
                url: '/api/clusters/' + this.model.id + '/changes',
                complete: _.bind(function() {
                    var complete = _.after(2, _.bind(this.scheduleUpdate, this));
                    this.model.get('tasks').fetch({data: {cluster_id: this.model.id}, complete: complete});
                    this.model.get('nodes').fetch({data: {cluster_id: this.model.id}, complete: complete});
                }, this)
            });
        },
        scheduleUpdate: function() {
            if (this.model.task('deploy', 'running')) {
                _.delay(_.bind(this.update, this), this.updateInterval);
            }
        },
        update: function() {
            if (this == app.page) {
                var complete = _.after(2, _.bind(this.scheduleUpdate, this));
                var task = this.model.task('deploy', 'running');
                if (task) {
                    task.fetch({complete: complete}).done(_.bind(this.refreshNotificationsAfterDeployment, this));
                    this.model.get('nodes').fetch({data: {cluster_id: this.model.id}, complete: complete});
                }
            }
        },
        refreshNotificationsAfterDeployment: function() {
            var task = this.model.task('deploy');
            if (task.get('status') != 'running') {
                app.navbar.notifications.collection.fetch();
            }
        },
        initialize: function(options) {
            _.defaults(this, options);
            this.model.bind('change:tasks', this.bindTasksEvents, this);
            this.bindTasksEvents();
            this.scheduleUpdate();
        },
        bindTasksEvents: function() {
            this.model.get('tasks').bind('reset', this.renderDeploymentControls, this);
        },
        renderDeploymentControls: function() {
            this.deploymentResult = new views.DeploymentResult({model: this.model});
            this.registerSubView(this.deploymentResult);
            this.$('.deployment-result').html(this.deploymentResult.render().el);
            this.deploymentControl = new views.DeploymentControl({model: this.model});
            this.registerSubView(this.deploymentControl);
            this.$('.deployment-control').html(this.deploymentControl.render().el);
        },
        render: function() {
            this.$el.html(this.template({
                cluster: this.model,
                tabs: this.tabs,
                activeTab: this.activeTab,
                renaming: this.renaming
            }));
            this.renderDeploymentControls();

            var tabs = {
                'nodes': views.NodesTab,
                'network': views.NetworkTab,
                'settings': views.SettingsTab,
                'actions': views.ActionsTab,
                'logs': views.LogsTab
            };
            if (_.has(tabs, this.activeTab)) {
                this.tab = new tabs[this.activeTab]({model: this.model});
                this.$('#tab-' + this.activeTab).html(this.tab.render().el);
                this.registerSubView(this.tab);
            }

            return this;
        }
    });

    views.DeploymentResult = Backbone.View.extend({
        template: _.template(deploymentResultTemplate),
        initialize: function(options) {
            var task = this.model.task('deploy');
            if (task) {
                task.bind('change:status', this.render, this);
            }
        },
        render: function() {
            this.$el.html(this.template({cluster: this.model}));
            return this;
        }
    });

    views.DeploymentControl = Backbone.View.extend({
        template: _.template(deploymentControlTemplate),
        initialize: function(options) {
            var task = this.model.task('deploy');
            if (task) {
                task.bind('change:status', this.render, this);
                task.bind('change:progress', this.updateProgress, this);
            }
        },
        updateProgress: function() {
            var task = this.model.task('deploy', 'running');
            if (task) {
                var progress = task.get('progress') || 0;
                this.$('.progress').attr('data-original-title', 'Deployment in progress, ' + progress + '% completed').tooltip('fixTitle');
                this.$('.bar').css('width', (progress > 10 ? progress : 10) + '%');
            }
        },
        render: function() {
            this.$('.progress').tooltip('destroy');
            this.$el.html(this.template({cluster: this.model}));
            this.updateProgress();
            return this;
        }
    });

    views.NodesTab = Backbone.View.extend({
        screen: null,
        scrollPositions: {},
        changeScreen: function(NewScreenView, screenOptions) {
            var options = _.extend({model: this.model, tab: this}, screenOptions || {});
            var newScreen = new NewScreenView(options);
            var oldScreen = this.screen;
            if (oldScreen) {
                if (oldScreen.keepScrollPosition) {
                    this.scrollPositions[oldScreen.screenName] = $(window).scrollTop();
                }
                oldScreen.$el.fadeOut('fast', _.bind(function() {
                    oldScreen.tearDown();
                    newScreen.render();
                    newScreen.$el.hide().fadeIn('fast');
                    this.$el.html(newScreen.el);
                    if (newScreen.keepScrollPosition && this.scrollPositions[newScreen.screenName]) {
                        $(window).scrollTop(this.scrollPositions[newScreen.screenName]);
                    }
                }, this));
            } else {
                this.$el.html(newScreen.render().el);
            }
            this.screen = newScreen;
            this.registerSubView(this.screen);
        },
        render: function() {
            this.$el.html('');
            this.changeScreen(views.NodesByRolesScreen);
            return this;
        }
    });

    views.NodesTabSummary = Backbone.View.extend({
        template: _.template(nodesTabSummaryTemplate),
        events: {
            'click .change-cluster-mode-btn:not(.disabled)': 'changeClusterMode',
            'click .change-cluster-type-btn:not(.disabled)': 'changeClusterType'
        },
        changeClusterMode: function() {
            var dialog = new dialogViews.ChangeClusterModeDialog({model: this.model});
            this.registerSubView(dialog);
            dialog.render();
        },
        changeClusterType: function() {
            var dialog = new dialogViews.ChangeClusterTypeDialog({model: this.model});
            this.registerSubView(dialog);
            dialog.render();
        },
        beforeTearDown: function() {
            this.$('[rel=tooltip]').tooltip('destroy');
        },
        render: function() {
            this.$('[rel=tooltip]').tooltip('destroy');
            this.$el.html(this.template({cluster: this.model}));
            return this;
        }
    });

    views.NodesByRolesScreen = Backbone.View.extend({
        className: 'nodes-by-roles-screen',
        screenName: 'nodes-by-roles',
        keepScrollPosition: true,
        initialize: function(options) {
            this.tab = options.tab;
            this.model.bind('change:mode change:type', this.render, this);
            this.model.bind('change:nodes', this.bindNodesEvents, this);
            this.bindNodesEvents();
            this.model.bind('change:tasks', this.bindTasksEvents, this);
            this.bindTasksEvents();
        },
        bindTasksEvents: function() {
            this.model.get('tasks').bind('reset', this.bindTaskEvents, this);
            this.bindTaskEvents();
        },
        bindTaskEvents: function() {
            var task = this.model.task('deploy', 'running');
            if (task) {
                task.bind('change:status', this.render, this);
                this.render();
            }
        },
        bindNodesEvents: function() {
            this.model.get('nodes').bind('reset', this.render, this);
        },
        render: function() {
            this.tearDownRegisteredSubViews();
            this.$el.html('');
            var summary = new views.NodesTabSummary({model: this.model});
            this.registerSubView(summary);
            this.$el.append(summary.render().el);
            var roles = this.model.availableRoles();
            _.each(roles, function(role, index) {
                var nodes = new models.Nodes(this.model.get('nodes').where({role: role}));
                nodes.cluster = this.model;
                var nodeListView = new views.NodeList({
                    collection: nodes,
                    role: role,
                    tab: this.tab,
                    size: role == 'controller' ? this.model.get('mode') == 'ha' ? 3 : 1 : 0
                });
                this.registerSubView(nodeListView);
                this.$el.append(nodeListView.render().el);
                if (index < roles.length - 1) {
                    this.$el.append('<hr>');
                }
            }, this);
            return this;
        }
    });

    views.EditNodesScreen = Backbone.View.extend({
        className: 'edit-nodes-screen',
        screenName: 'edit-nodes',
        keepScrollPosition: false,
        template: _.template(editNodesScreenTemplate),
        events: {
            'click .btn-discard': 'discardChanges',
            'click .btn-apply:not([disabled])': 'applyChanges',
            'click .nodebox': 'toggleNode',
            'click .select-all-tumbler': 'selectAll'
        },
        toggleNode: function(e) {
            if (this.limit !== null && $(e.currentTarget).is('.node-to-' + this.action + '-unchecked') && this.$('.node-to-' + this.action + '-checked').length >= this.limit) {
                return;
            }
            $(e.currentTarget).toggleClass('node-to-' + this.action + '-checked').toggleClass('node-to-' + this.action + '-unchecked');
            this.calculateSelectAllTumblerState();
            this.calculateNotChosenNodesAvailability();
            this.calculateApplyButtonAvailability();
            this.forceWebkitRedraw();
        },
        selectAll: function(e) {
            var checked = $(e.currentTarget).is(':checked');
            this.$('.nodebox').toggleClass('node-to-' + this.action + '-checked', checked).toggleClass('node-to-' + this.action + '-unchecked', !checked);
            this.calculateApplyButtonAvailability();
            this.forceWebkitRedraw();
        },
        forceWebkitRedraw: function() {
            if ($.browser.webkit) {
                this.$('.nodebox').each(function() {
                    this.style.webkitTransform = 'scale(1)';
                    var dummy = this.offsetHeight;
                    this.style.webkitTransform = '';
                });
            }
        },
        calculateSelectAllTumblerState: function() {
            this.$('.select-all-tumbler').attr('checked', this.nodes.length == this.$('.node-to-' + this.action + '-checked').length);
        },
        calculateNotChosenNodesAvailability: function() {
            if (this.limit !== null) {
                var chosenNodesCount = this.$('.node-to-' + this.action + '-checked').length;
                var notChosenNodes = this.$('.nodebox:not(.node-to-' + this.action + '-checked)');
                notChosenNodes.toggleClass('node-not-checkable', chosenNodesCount >= this.limit);
            }
        },
        calculateApplyButtonAvailability: function() {
            this.$('.btn-apply').attr('disabled', !this.getChosenNodesIds());
        },
        discardChanges: function() {
            this.tab.changeScreen(views.NodesByRolesScreen);
        },
        applyChanges: function(e) {
            this.$('.btn-apply').attr('disabled', true);
            var nodes = new models.Nodes(this.getChosenNodes());
            this.modifyNodes(nodes);
            Backbone.sync('update', nodes).done(_.bind(function() {
                this.tab.changeScreen(views.NodesByRolesScreen);
                this.model.get('nodes').fetch({data: {cluster_id: this.model.id}});
                app.navbar.stats.nodes.fetch();
            }, this));
        },
        getChosenNodesIds: function() {
            return this.$('.node-to-' + this.action + '-checked').map(function() {return parseInt($(this).attr('data-node-id'), 10);}).get();
        },
        getChosenNodes: function() {
            var chosenNodesIds = this.getChosenNodesIds();
            return this.nodes.filter(function(node) {return _.contains(chosenNodesIds, node.id);});
        },
        initialize: function(options) {
            _.defaults(this, options);
            this.nodes = new models.Nodes();
        },
        renderNodes: function() {
            this.tearDownRegisteredSubViews();
            var nodesContainer = this.$('.available-nodes');
            if (this.nodes.length) {
                nodesContainer.html('');
                this.nodes.each(function(node) {
                    var options = {model: node};
                    if (this.action == 'add') {
                        options.selectableForAddition = true;
                    } else if (this.action == 'delete') {
                        options.selectableForDeletion = true;
                    }
                    var nodeView = new views.Node(options);
                    this.registerSubView(nodeView);
                    nodesContainer.append(nodeView.render().el);
                    if (node.get(this.flag)) {
                        nodeView.$('.nodebox[data-node-id=' + node.id + ']').addClass('node-to-' + this.action + '-checked').removeClass('node-to-' + this.action + '-unchecked');
                    }
                }, this);
            } else {
                nodesContainer.html('<div class="span12">No nodes available</div>');
            }
        },
        render: function() {
            this.$el.html(this.template({nodes: this.nodes, role: this.role, action: this.action, limit: this.limit}));
            if (!this.nodes.deferred || this.nodes.deferred.state() != 'pending') {
                this.renderNodes();
            }
            return this;
        }
    });

    views.AddNodesScreen = views.EditNodesScreen.extend({
        className: 'add-nodes-screen',
        action: 'add',
        flag: 'pending_addition',
        initialize: function(options) {
            this.constructor.__super__.initialize.apply(this, arguments);
            this.nodes = new models.Nodes();
            this.nodes.deferred = this.nodes.fetch({data: {cluster_id: ''}}).done(_.bind(function() {
                this.nodes.add(this.model.get('nodes').where({role: options.role, pending_deletion: true}), {at: 0});
                this.render();
            }, this));
        },
        modifyNodes: function(nodes) {
            nodes.each(function(node) {
                if (node.get('pending_deletion')) {
                    node.set({pending_deletion: false}, {silent: true});
                } else {
                    node.set({
                        cluster_id: this.model.id,
                        role: this.role,
                        pending_addition: true
                    }, {silent: true});
                }
            }, this);
            nodes.toJSON = function(options) {
                return this.map(function(node) {
                    return _.pick(node.attributes, 'id', 'cluster_id', 'role', 'pending_addition', 'pending_deletion');
                });
            };
        }
    });

    views.DeleteNodesScreen = views.EditNodesScreen.extend({
        className: 'delete-nodes-screen',
        action: 'delete',
        flag: 'pending_deletion',
        initialize: function(options) {
            this.constructor.__super__.initialize.apply(this, arguments);
            this.nodes = new models.Nodes(this.model.get('nodes').filter(function(node) {
                return node.get('role') == options.role && (node.get('pending_addition') || !node.get('pending_deletion'));
            }));
        },
        modifyNodes: function(nodes) {
            nodes.each(function(node) {
                if (node.get('pending_addition')) {
                    node.set({
                        cluster_id: null,
                        role: null,
                        pending_addition: false
                    }, {silent: true});
                } else {
                    node.set({pending_deletion: true}, {silent: true});
                }
            }, this);
            nodes.toJSON = function(options) {
                return this.map(function(node) {
                    return _.pick(node.attributes, 'id', 'cluster_id', 'role', 'pending_addition', 'pending_deletion');
                });
            };
        }
    });

    views.NodeList = Backbone.View.extend({
        className: 'node-list',
        template: _.template(nodeListTemplate),
        events: {
            'click .btn-add-nodes:not(.disabled)': 'addNodes',
            'click .btn-delete-nodes:not(.disabled)': 'deleteNodes'
        },
        addNodes: function() {
            var limit = null;
            if (this.size && this.collection.cluster.get('mode') != 'ha') {
                limit = this.size - this.collection.nodesAfterDeployment().length;
                if (limit <= 0) {
                    limit = 0;
                }
            }
            this.tab.changeScreen(views.AddNodesScreen, {role: this.role, limit: limit});
        },
        deleteNodes: function() {
            this.tab.changeScreen(views.DeleteNodesScreen, {role: this.role, limit: null});
        },
        initialize: function(options) {
            _.defaults(this, options);
        },
        render: function() {
            var hasChanges = this.collection.hasChanges();
            var currentNodes = this.collection.currentNodes();
            var nodesAfterDeployment = this.collection.nodesAfterDeployment();
            this.$el.html(this.template({
                nodes: this.collection,
                role: this.role,
                size: this.size,
                hasChanges: hasChanges,
                currentNodes: currentNodes,
                nodesAfterDeployment: nodesAfterDeployment
            }));
            this.$el.addClass('node-list-' + this.role);
            if (this.collection.length || this.size) {
                var container = this.$('.node-list-container');
                this.collection.each(function(node) {
                    var nodeView = new views.Node({model: node, renameable: !this.collection.cluster.task('deploy', 'running')});
                    this.registerSubView(nodeView);
                    container.append(nodeView.render().el);
                }, this);
                if (nodesAfterDeployment.length < this.size) {
                    _(this.size - nodesAfterDeployment.length).times(function() {
                        container.append('<div class="span2 nodebox nodeplaceholder"></div>');
                    });
                }
            }
            return this;
        }
    });

    views.Node = Backbone.View.extend({
        template: _.template(nodeTemplate),
        events: {
            'click .node-name': 'startNodeRenaming',
            'keydown .node-name-editable': 'onNodeNameInputKeydown'
        },
        startNodeRenaming: function() {
            if (!this.renameable || this.renaming || this.model.collection.cluster.task('deploy', 'running')) {return;}
            $('html').off(this.eventNamespace);
            $('html').on(this.eventNamespace, _.after(2, _.bind(function(e) {
                if (!$(e.target).closest(this.$el).length) {
                    this.endNodeRenaming();
                }
            }, this)));
            this.renaming = true;
            this.render();
            this.$('.node-name-editable input').focus();
        },
        endNodeRenaming: function() {
            $('html').off(this.eventNamespace);
            this.renaming = false;
            this.render();
        },
        applyNewNodeName: function() {
            var name = $.trim(this.$('.node-name-editable input').val());
            if (name != this.model.get('name')) {
                this.$('.node-name-editable input').attr('disabled', true);
                this.model.update({name: name}, {complete: this.endNodeRenaming, context: this});
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
        beforeTearDown: function() {
            $('html').off(this.eventNamespace);
        },
        initialize: function(options) {
            _.defaults(this, options);
            this.renaming = false;
            this.eventNamespace = 'click.editnodename' + this.model.id;
            this.model.bind('change', this.render, this);
        },
        render: function() {
            this.$el.html(this.template({
                node: this.model,
                renaming: this.renaming,
                renameable: this.renameable,
                selectableForAddition: this.selectableForAddition,
                selectableForDeletion: this.selectableForDeletion
            }));
            return this;
        }
    });

    views.NetworkTab = Backbone.View.extend({
        template: _.template(networkTabTemplate),
        viewModeTemplate: _.template(networkTabViewModeTemplate),
        events: {
            'keydown .row input': 'enableApplyButton',
            'click .apply-btn:not([disabled])': 'apply',
            'click .nav a': 'changeMode'
        },
        enableApplyButton: function() {
            this.$('.apply-btn').attr('disabled', false);
        },
        apply: function() {
            var valid = true;
            this.$('.help-inline').text('');
            this.$('.control-group').removeClass('error');
            this.networks.each(function(network) {
                var row = this.$('.control-group[data-network-name=' + network.get('name') + ']');
                network.on('error', function(model, errors) {
                    valid = false;
                    $('.network-error .help-inline', row).text(errors.cidr || errors.vlan_id);
                    row.addClass('error');
                }, this);
                network.set({
                    cidr: $('.network-cidr input', row).val(),
                    vlan_id: parseInt($('.network-vlan input', row).val(), 10)
                });
            }, this);
            if (valid) {
                Backbone.sync('update', this.networks);
                this.$('.apply-btn').attr('disabled', true);
            }
        },
        changeMode: function(e) {
            e.preventDefault();
            /*
            var targetLi = $(e.currentTarget).parent();
            if (!targetLi.hasClass('active')) {
                if (targetLi.hasClass('network-view')) {
                    this.$('.nav li').toggleClass('active');
                    this.$('.network-tab-content').html(this.viewModeTemplate({cluster: this.model, networks: this.networks}));
                } else {
                    this.render();
                }
            }
            */
        },
        bindTaskEvents: function() {
            var task = this.model.task('deploy', 'running');
            if (task) {
                task.bind('change:status', this.render, this);
            }
        },
        bindEvents: function() {
            this.model.get('tasks').bind('reset', this.bindTaskEvents, this);
            this.bindTaskEvents();
        },
        initialize: function(options) {
            this.model.get('tasks').bind('remove reset', this.renderVerificationControls, this);
            this.model.bind('change:tasks', this.bindEvents, this);
            this.bindEvents();
            if (!this.model.get('networks')) {
                this.networks = new models.Networks();
                this.networks.deferred = this.networks.fetch({data: {cluster_id: this.model.id}});
                this.networks.deferred.done(_.bind(this.render, this));
                this.model.set({'networks': this.networks}, {silent: true});
            } else {
                this.networks = this.model.get('networks');
            }
        },
        renderVerificationControls: function() {
            var verificationView = new views.NetworkTabVerification({model: this.model, networks: this.networks});
            this.registerSubView(verificationView);
            this.$('.verify-network').html(verificationView.render().el);
        },
        render: function() {
            this.$el.html(this.template({cluster: this.model, networks: this.networks}));
            this.renderVerificationControls();
            return this;
        }
    });

    views.NetworkTabVerification = Backbone.View.extend({
        updateInterval: 3000,
        template: _.template(networkTabVerificationTemplate),
        events: {
            'click .verify-networks-btn:not([disabled])': 'verifyNetworks',
            'click .verification-result-btn': 'dismissVerificationResult'
        },
        scheduleUpdate: function() {
            if (this.model.task('verify_networks', 'running')) {
                _.delay(_.bind(this.update, this), this.updateInterval);
            }
        },
        update: function(force) {
            var task = this.model.task('verify_networks', 'running');
            if (task && (force || app.page.$el.find(this.el).length)) {
                task.fetch({complete: _.bind(this.scheduleUpdate, this)});
            }
        },
        verifyNetworks: function() {
            this.$('.verify-networks-btn').attr('disabled', true);
            var task = new models.Task();
            task.save({}, {
                type: 'PUT',
                url: '/api/clusters/' + this.model.id + '/verify/networks',
                complete: _.bind(function() {
                    this.model.get('tasks').fetch({data: {cluster_id: this.model.id}});
                }, this)
            });
        },
        dismissVerificationResult: function() {
            var task = this.model.task('verify_networks');
            this.model.get('tasks').remove(task);
            task.destroy();
        },
        updateProgress: function() {
            var task = this.model.task('verify_networks', 'running');
            if (task) {
                var progress = task.get('progress') || 0;
                this.$('.progress').attr('data-original-title', 'Verifying networks, ' + progress + '% completed').tooltip('fixTitle');
                this.$('.bar').css('width', (progress > 10 ? progress : 10) + '%');
            }
        },
        initialize: function(options) {
            var task = this.model.task('verify_networks');
            if (task) {
                task.bind('change:status', this.render, this);
                task.bind('change:progress', this.updateProgress, this);
                this.update(true);
            }
        },
        render: function() {
            this.$('.progress').tooltip('destroy');
            this.$el.html(this.template({cluster: this.model, networks: this.options.networks}));
            this.updateProgress();
            return this;
        }
    });

    views.SettingsTab = Backbone.View.extend({
        template: _.template(settingsTabTemplate),
        events: {
            'click .btn-apply-changes:not([disabled])': 'applyChanges',
            'click .btn-revert-changes:not([disabled])': 'revertChanges',
            'click .btn-set-defaults:not([disabled])': 'setDefaults'
        },
        defaultButtonsState: function(buttonState) {
            this.$('.settings-editable .btn').attr('disabled', buttonState);
            this.$('.btn-set-defaults').attr('disabled', !buttonState);
        },
        disableControls: function() {
            this.$('.settings-editable .btn, .settings-editable input').attr('disabled', true);
        },
        collectData: function(parentEl, changedData) {
            var model = this, param;
            _.each(parentEl.children().children('.wrapper'), function(el) {
                if ($(el).data('nested')) {
                    param = $(el).find('legend:first').text();
                    changedData[param] = {};
                    model.collectData($(el), changedData[param]);
                } else {
                    param = $(el).find('input');
                    changedData[param.attr('name')] = param.val();
                }
            });
        },
        applyChanges: function() {
            var changedData = {};
            this.collectData(this.$('.settings-content'), changedData);
            this.model.get('settings').update({editable: changedData}, {
                url: '/api/clusters/' + this.model.id + '/attributes',
                complete: _.bind(this.render, this)
            });
            this.disableControls();
        },
        parseSettings: function(settings) {
            this.tearDownRegisteredSubViews();
            if (_.isObject(settings)) {
                this.$('.settings-content').html('');
                _.each(_.keys(settings), function(setting) {
                    var settingsGroupView = new views.SettingsGroup({legend: setting, settings: settings[setting], model: this.model});
                    this.registerSubView(settingsGroupView);
                    this.$('.settings-content').append(settingsGroupView.render().el);
                }, this);
            }
        },
        revertChanges: function() {
            this.parseSettings(this.model.get('settings').get('editable'));
            this.defaultButtonsState(true);
        },
        setDefaults: function() {
            this.model.get('settings').update({}, {
                url: '/api/clusters/' + this.model.id + '/attributes/defaults',
                complete: _.bind(this.render, this)
            });
            this.disableControls();
        },
        render: function () {
            this.$el.html(this.template({settings: this.model.get('settings'), cluster: this.model}));
            if (this.model.get('settings').deferred.state() != 'pending') {
                var settings = this.model.get('settings').get('editable');
                this.parseSettings(settings);
            }
            return this;
        },
        bindTaskEvents: function() {
            var task = this.model.task('deploy', 'running');
            if (task) {
                task.bind('change:status', this.render, this);
            }
        },
        bindEvents: function() {
            this.model.get('tasks').bind('reset', this.bindTaskEvents, this);
            this.bindTaskEvents();
        },
        initialize: function() {
            this.model.bind('change:tasks', this.bindEvents, this);
            this.bindEvents();
            if (!this.model.get('settings')) {
                this.model.set({'settings': new models.Settings()}, {silent: true});
                this.model.get('settings').deferred = this.model.get('settings').fetch({
                    url: '/api/clusters/' + this.model.id + '/attributes'
                });
                this.model.get('settings').deferred.done(_.bind(this.render, this));
            }
        }
    });

    views.SettingsGroup = Backbone.View.extend({
        template: _.template(settingsGroupTemplate),
        events: {
            'keydown input': 'hasChanges'
        },
        hasChanges: function() {
            $('.settings-editable .btn').attr('disabled', false);
        },
        initialize: function(options) {
            _.defaults(this, options);
        },
        render: function() {
            this.$el.html(this.template({settings: this.settings, legend: this.legend, cluster: this.model}));
            return this;
        }
    });

    views.ActionsTab = Backbone.View.extend({
        template: _.template(actionsTabTemplate),
        events: {
            'click .rename-cluster-form .apply-name-btn': 'applyNewClusterName',
            'keydown .rename-cluster-form input': 'onClusterNameInputKeydown',
            'click .delete-cluster-form .delete-cluster-btn': 'deleteCluster'
        },
        applyNewClusterName: function() {
            var name = $.trim(this.$('.rename-cluster-form input').val());
            if (name != '' && name != this.model.get('name')) {
                this.$('.rename-cluster-form input, .rename-cluster-form .apply-name-btn').attr('disabled', true);
                this.model.update({name: name}, {
                    complete: function() {
                            app.breadcrumb.setPath(['Home', '#'], ['OpenStack Installations', '#clusters'], this.model.get('name'));
                            this.render();
                        },
                    context: this
                });
            }
        },
        onClusterNameInputKeydown: function(e) {
            if (e.which == 13) {
                this.applyNewClusterName();
            }
        },
        deleteCluster: function() {
            var deleteClusterDialogView = new dialogViews.RemoveClusterDialog({model: this.model});
            this.registerSubView(deleteClusterDialogView);
            deleteClusterDialogView.render();
        },
        initialize: function() {
            this.model.bind('change:name', this.render, this);
        },
        render: function() {
            this.$el.html(this.template({cluster: this.model}));
            return this;
        }
    });

    views.LogsTab = Backbone.View.extend({
        template: _.template(logsTabTemplate),
        render: function() {
            this.$el.html(this.template());
            return this;
        }
    });

    return views;
});
