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
    'text!templates/cluster/network_tab_summary.html',
    'text!templates/cluster/verify_network_control.html',
    'text!templates/cluster/settings_tab.html',
    'text!templates/cluster/settings_group.html',
    'text!templates/cluster/actions_tab.html'
],
function(models, dialogViews, clusterPageTemplate, deploymentResultTemplate, deploymentControlTemplate, nodesTabSummaryTemplate, editNodesScreenTemplate, nodeListTemplate, nodeTemplate, networkTabSummaryTemplate, networkTabVerificationTemplate, settingsTabTemplate, settingsGroupTemplate, actionsTabTemplate) {
    'use strict';

    var views = {};

    views.ClusterPage = Backbone.View.extend({
        updateInterval: 5000,
        template: _.template(clusterPageTemplate),
        events: {
            'click .task-result .close': 'dismissTaskResult',
            'click .deploy-btn:not([disabled])': 'deployCluster'
        },
        dismissTaskResult: function() {
            this.$('.task-result').remove();
            this.model.task('deploy').destroy();
        },
        deployCluster: function() {
            this.$('.deploy-btn').attr('disabled', true);
            var task = new models.Task();
            task.save({}, {
                type: 'PUT',
                url: '/api/clusters/' + this.model.id + '/changes',
                complete: _.bind(function() {
                    this.model.get('tasks').fetch({data: {cluster_id: this.model.id}}).done(_.bind(this.scheduleUpdate, this));
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
                    task.fetch({complete: complete});
                    this.model.get('nodes').fetch({data: {cluster_id: this.model.id}, complete: complete});
                }
            }
        },
        initialize: function(options) {
            _.defaults(this, options);
            this.model.get('tasks').bind('add remove reset', this.renderDeploymentControls, this);
            this.model.bind('destroy', function() {
                app.navbar.stats.nodes.fetch();
                app.navigate('#clusters', {trigger: true});
            }, this);
            this.scheduleUpdate();
        },
        renderDeploymentControls: function() {
            this.$('.deployment-result').html(new views.DeploymentResult({model: this.model}).render().el);
            this.$('.deployment-control').html(new views.DeploymentControl({model: this.model}).render().el);
        },
        render: function() {
            this.$el.html(this.template({
                cluster: this.model,
                tabs: this.tabs,
                activeTab: this.tab,
                renaming: this.renaming
            }));
            this.renderDeploymentControls();

            var tabs = {
                'nodes': views.NodesTab,
                'network': views.NetworkTab,
                'settings': views.SettingsTab,
                'actions': views.ActionsTab
            };
            if (_.has(tabs, this.tab)) {
                this.$('#tab-' + this.tab).html(new tabs[this.tab]({model: this.model}).render().el);
            }

            return this;
        }
    });

    views.DeploymentResult = Backbone.View.extend({
        template: _.template(deploymentResultTemplate),
        initialize: function(options) {
            var task = this.model.task('deploy');
            if (task) {
                task.bind('change', this.render, this);
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
                    oldScreen.remove();
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
            (new dialogViews.ChangeClusterModeDialog({model: this.model})).render();
        },
        changeClusterType: function() {
            (new dialogViews.ChangeClusterTypeDialog({model: this.model})).render();
        },
        render: function() {
            this.$el.html(this.template({cluster: this.model}));
            return this;
        }
    });

    views.NodesByRolesScreen = Backbone.View.extend({
        screenName: 'nodes-by-roles',
        keepScrollPosition: true,
        initialize: function(options) {
            this.tab = options.tab;
            this.model.bind('change:mode change:type', this.render, this);
            this.model.get('nodes').bind('add remove reset', this.render, this);
        },
        render: function() {
            this.$el.html('');
            this.$el.append((new views.NodesTabSummary({model: this.model})).render().el);
            var roles = this.model.availableRoles();
            _.each(roles, function(role, index) {
                var nodes = new models.Nodes(this.model.get('nodes').where({role: role}));
                nodes.cluster = this.model;
                var nodeListView = new views.NodeList({
                    collection: nodes,
                    role: role,
                    tab: this.tab,
                    size: role == 'controller' ? this.model.get('mode') == 'ha' ? this.model.get('redundancy') : 1 : 0
                });
                this.$el.append(nodeListView.render().el);
                if (index < roles.length - 1) {
                    this.$el.append('<hr>');
                }
            }, this);
            return this;
        }
    });

    views.EditNodesScreen = Backbone.View.extend({
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
            if (this.limit && $(e.currentTarget).is('.node-to-' + this.action + '-unchecked') && this.$('.node-to-' + this.action + '-checked').length >= this.limit) {
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
            this.forceWebkitRedraw();
            this.calculateApplyButtonAvailability();
        },
        forceWebkitRedraw: function() {
            this.$('.nodebox').each(function() {
                this.style.webkitTransform = 'scale(1)';
                var dummy = this.offsetHeight;
                this.style.webkitTransform = '';
            });
        },
        calculateSelectAllTumblerState: function() {
            this.$('.select-all-tumbler').attr('checked', this.availableNodes.length == this.$('.node-to-' + this.action + '-checked').length);
        },
        calculateNotChosenNodesAvailability: function() {
            if (this.limit) {
                var chosenNodesCount = this.$('.node-to-' + this.action + '-checked').length;
                var notChosenNodes = this.$('.nodebox:not(.node-to-' + this.action + '-checked)');
                notChosenNodes.toggleClass('node-not-checkable', chosenNodesCount >= this.limit);
            }
        },
        calculateApplyButtonAvailability: function() {
            this.$('.btn-apply').attr('disabled', !this.$('.node-to-' + this.action + '-checked').length);
        },
        discardChanges: function() {
            this.tab.changeScreen(views.NodesByRolesScreen);
        },
        applyChanges: function(e) {
            this.$('.btn-apply').attr('disabled', true);
            var chosenNodes = this.getChosenNodes();
            this.modifyNodes(chosenNodes);
            Backbone.sync('update', chosenNodes).done(_.bind(function() {
                this.tab.changeScreen(views.NodesByRolesScreen);
                this.model.fetch();
                app.navbar.stats.nodes.fetch();
            }, this));
        },
        getChosenNodes: function() {
            var chosenNodesIds = this.$('.node-to-' + this.action + '-checked').map(function() {return parseInt($(this).attr('data-node-id'), 10);}).get();
            var chosenNodes = this.availableNodes.filter(function(node) {return _.contains(chosenNodesIds, node.id);});
            return new models.Nodes(chosenNodes);
        },
        initialize: function(options) {
            _.defaults(this, options);
            this.availableNodes = new models.Nodes();
        },
        renderNodes: function() {
            var nodesContainer = this.$('.available-nodes');
            if (this.availableNodes.length) {
                nodesContainer.html('');
                this.availableNodes.each(function(node) {
                    var options = {model: node};
                    if (this.action == 'add') {
                        options.selectableForAddition = true;
                    } else if (this.action == 'delete') {
                        options.selectableForDeletion = true;
                    }
                    nodesContainer.append(new views.Node(options).render().el);
                }, this);
            } else {
                nodesContainer.html('<div class="span12">No nodes available</div>');
            }
        },
        render: function() {
            this.$el.html(this.template({nodes: this.availableNodes, role: this.role, action: this.action, limit: this.limit}));
            if (this.availableNodes.deferred) {
                this.availableNodes.deferred.done(_.bind(this.renderNodes, this));
            } else {
                this.renderNodes();
            }
            return this;
        }
    });

    views.AddNodesScreen = views.EditNodesScreen.extend({
        action: 'add',
        initialize: function(options) {
            this.constructor.__super__.initialize.apply(this, arguments);
            this.availableNodes = new models.Nodes();
            this.availableNodes.deferred = this.availableNodes.fetch({data: {cluster_id: ''}});
        },
        modifyNodes: function(nodes) {
            nodes.each(function(node) {
                node.set({
                    cluster_id: this.model.id,
                    role: this.role,
                    redeployment_needed: true
                });
            }, this);
            nodes.toJSON = function(options) {
                return this.map(function(node) {
                    return _.pick(node.attributes, 'id', 'cluster_id', 'role', 'redeployment_needed');
                });
            };
        }
    });

    views.DeleteNodesScreen = views.EditNodesScreen.extend({
        action: 'delete',
        initialize: function(options) {
            this.constructor.__super__.initialize.apply(this, arguments);
            this.availableNodes = new models.Nodes(this.model.get('nodes').where({role: options.role}));
        },
        applyChanges: function() {
            if (confirm('Do you really want to delete these nodes?')) {
                this.constructor.__super__.applyChanges.call(this);
            }
        },
        modifyNodes: function(nodes) {
            nodes.each(function(node) {
                node.set({
                    cluster_id: null,
                    role: null,
                    redeployment_needed: false
                });
            }, this);
            nodes.toJSON = function(options) {
                return this.map(function(node) {
                    return _.pick(node.attributes, 'id', 'cluster_id', 'role', 'redeployment_needed');
                });
            };
        }
    });

    views.NodeList = Backbone.View.extend({
        template: _.template(nodeListTemplate),
        events: {
            'click .btn-add-nodes:not(.disabled)': 'addNodes',
            'click .btn-delete-nodes:not(.disabled)': 'deleteNodes'
        },
        addNodes: function() {
            var limit = this.size - this.collection.length;
            if (limit <= 0) {
                limit = 0;
            }
            this.tab.changeScreen(views.AddNodesScreen, {role: this.role, limit: limit});
        },
        deleteNodes: function() {
            this.tab.changeScreen(views.DeleteNodesScreen, {role: this.role});
        },
        initialize: function(options) {
            _.defaults(this, options);
        },
        render: function() {
            this.$el.html(this.template({nodes: this.collection, role: this.role, size: this.size}));
            if (this.collection.length || this.size) {
                var container = this.$('.node-list-container');
                this.collection.each(function(node) {
                    container.append(new views.Node({model: node, renameable: !this.collection.cluster.task('deploy', 'running')}).render().el);
                }, this);
                if (this.collection.length < this.size) {
                    _(this.size - this.collection.length).times(function() {
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
        render: function() {
            this.$el.html('');
            this.$el.append((new views.NetworkTabSummary({model: this.model})).render().el);
            // other contents TBD
            return this;
        }
    });

    views.NetworkTabSummary = Backbone.View.extend({
        template: _.template(networkTabSummaryTemplate),
        events: {
            'click .change-network-settings-btn': 'changeNetworkSettings'
        },
        changeNetworkSettings: function() {
            (new dialogViews.ChangeNetworkSettingsDialog({model: this.model})).render();
        },
        initialize: function(options) {
            this.model.get('tasks').bind('add remove reset', this.renderVerificationControls, this);
        },
        renderVerificationControls: function() {
            this.$('.verify-network').html((new views.NetworkTabVerification({model: this.model})).render().el);
        },
        render: function() {
            this.$el.html(this.template({cluster: this.model}));
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
            this.$el.html(this.template({cluster: this.model}));
            this.updateProgress();
            return this;
        }
    });

    views.SettingsTab = Backbone.View.extend({
        template: _.template(settingsTabTemplate),
        events: {
            'click .btn-apply-changes': 'applyChanges',
            'click .btn-revert-changes': 'revertChanges',
            'click .btn-set-defaults': 'setDefaults'
        },
        defaultButtonsState: function(buttonState) {
            this.$('.settings-editable .btn').attr('disabled', buttonState);
            this.$('.btn-set-defaults').attr('disabled', !buttonState);
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
                url: '/api/clusters/' + this.model.id + '/attributes'
            });
            this.defaultButtonsState(true);
        },
        parseSettings: function(settings) {
            if (_.isObject(settings)) {
                this.$('.settings-content').html('');
                _.each(_.keys(settings), function(setting) {
                    var settingsGroupView = new views.SettingsGroup({legend: setting, settings: settings[setting]});
                    this.$('.settings-content').append(settingsGroupView.render().el);
                }, this);
            }
        },
        revertChanges: function() {
            this.parseSettings(this.model.get('settings').get('editable'));
            this.defaultButtonsState(true);
        },
        setDefaults: function() {
            this.parseSettings(this.model.get('settings').get('defaults'));
            this.defaultButtonsState(false);
        },
        render: function () {
            this.$el.html(this.template({settings: this.model.get('settings')}));
            if (this.model.get('settings').deferred.state() != 'pending') {
                var settings = this.model.get('settings').get('editable');
                this.parseSettings(settings);
            }
            return this;
        },
        initialize: function() {
            if (!this.model.get('settings')) {
                this.model.set({'settings': new models.Settings()}, {silent: true});
                this.model.get('settings').deferred = this.model.get('settings').fetch({
                    url: '/api/clusters/' + this.model.id + '/attributes'
                });
                this.model.get('settings').deferred.done(_.bind(this.render, this));
                // also need to fetch defaults attributes
            }
        }
    });

    views.SettingsGroup = Backbone.View.extend({
        template: _.template(settingsGroupTemplate),
        events: {
            'keydown input': 'hasChanges'
        },
        hasChanges: function(el) {
            $('.settings-editable .btn').attr('disabled', false);
        },
        initialize: function(options) {
            this.settings = options.settings;
            this.legend = options.legend;
        },
        render: function() {
            /*
                // fake used to test a large nesting level
                var fake = '{"admin_tenant1": "admin1","admin_tenant2":{"admin_tenant3":"admin3"},"admin_tenant4":{"admin_tenant5":"admin3"}}';
                this.$el.html(this.template({settings: $.parseJSON(fake), legend: this.options.legend}));
            */
            this.$el.html(this.template({settings: this.settings, legend: this.legend}));
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
                this.model.update({name: name}, {complete: this.render, context: this});
            }
        },
        onClusterNameInputKeydown: function(e) {
            if (e.which == 13) {
                this.applyNewClusterName();
            }
        },
        deleteCluster: function() {
            if (confirm('Do you really want to delete this cluster?')) {
                this.model.destroy();
            }
        },
        initialize: function() {
            this.model.bind('change:name', this.render, this);
        },
        render: function() {
            this.$el.html(this.template({cluster: this.model}));
            return this;
        }
    });

    return views;
});
