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
    'verify_network_control.html'
],
function(models, dialogViews, clusterPageTemplate, deploymentResultTemplate, deploymentControlTemplate, nodesTabSummaryTemplate, editNodesScreenTemplate, nodeListTemplate, nodeTemplate, networkTabSummaryTemplate, networkTabVerificationTemplate, settingsTabTemplate, settingsGroupTemplate) {
    var views = {};

    views.ClusterPage = Backbone.View.extend({
        updateInterval: 5000,
        template: _.template(clusterPageTemplate),
        events: {
            'click .rename-cluster-btn': 'startClusterRenaming',
            'click .cluster-name-editable .discard-renaming-btn': 'endClusterRenaming',
            'click .cluster-name-editable .apply-name-btn': 'applyNewClusterName',
            'keydown .cluster-name-editable input': 'onClusterNameInputKeydown',
            'click .delete-cluster-btn': 'deleteCluster',
            'click .task-result .close': 'dismissTaskResult',
            'click .deploy-btn:not([disabled])': 'deployCluster'
        },
        startClusterRenaming: function() {
            this.renaming = true;
            this.$('.cluster-name-editable').show();
            this.$('.cluster-name-uneditable').hide();
            this.$('.cluster-name-editable input').val(this.model.get('name')).focus();
        },
        endClusterRenaming: function() {
            this.renaming = false;
            this.$('.cluster-name-editable').hide();
            this.$('.cluster-name-uneditable').show();
        },
        applyNewClusterName: function() {
            var name = $.trim(this.$('.cluster-name-editable input').val());
            if (name != '' && name != this.model.get('name')) {
                this.$('.cluster-name-editable input, .cluster-name-editable button').attr('disabled', true);
                this.model.update({name: name}, {complete: this.endClusterRenaming, context: this});
            } else {
                this.endClusterRenaming();
            }
        },
        onClusterNameInputKeydown: function(e) {
            if (e.which == 13) {
                this.applyNewClusterName();
            } else if (e.which == 27) {
                this.endClusterRenaming();
            }
        },
        deleteCluster: function() {
            if (confirm('Do you really want to delete this cluster?')) {
                this.model.destroy();
            }
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
                    this.model.fetch().done(_.bind(this.scheduleUpdate, this));
                }, this)
            });
        },
        initialize: function(options) {
            _.defaults(this, options);
            this.model.bind('change', this.render, this);
            this.model.bind('destroy', function() {
                app.navigate('#clusters', {trigger: true});
            }, this);
            this.scheduleUpdate();
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
                    this.model.get('nodes').fetch({complete: complete});
                }
            }
        },
        render: function() {
            this.$el.html(this.template({
                cluster: this.model,
                tabs: this.tabs,
                activeTab: this.tab,
                renaming: this.renaming
            }));

            this.$('.deployment-result').html(new views.DeploymentResult({model: this.model}).render().el);
            this.$('.deployment-control').html(new views.DeploymentControl({model: this.model}).render().el);

            var tabContainer = this.$('#tab-' + this.tab);
            if (this.tab == 'nodes') {
                tabContainer.html(new views.NodesTab({model: this.model}).render().el);
            } else if (this.tab == 'network') {
                tabContainer.html(new views.NetworkTab({model: this.model}).render().el);
            } else if (this.tab == 'settings') {
                tabContainer.html(new views.SettingsTab({model: this.model, settings: this.settings}).render().el);
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
        changeScreen: function(NewScreenView, screenOptions) {
            var options = _.extend({model: this.model, tab: this}, screenOptions || {});
            var newScreen = new NewScreenView(options);
            var oldScreen = this.screen;
            if (oldScreen) {
                oldScreen.$el.fadeOut('fast', _.bind(function() {
                    oldScreen.remove();
                    newScreen.render();
                    newScreen.$el.hide().fadeIn('fast');
                    this.$el.html(newScreen.el);
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
        initialize: function(options) {
            this.tab = options.tab;
            this.model.get('nodes').bind('reset', this.render, this);
            this.model.get('nodes').bind('add', this.render, this);
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
                    tab: this.tab
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
        template: _.template(editNodesScreenTemplate),
        events: {
            'click .btn-discard': 'discardChanges',
            'click .btn-apply:not([disabled])': 'applyChanges',
            'click .nodebox': 'toggleNode',
            'click .select-all-btn': 'selectAll'
        },
        toggleNode: function(e) {
            $(e.currentTarget).toggleClass('node-to-' + this.action + '-checked').toggleClass('node-to-' + this.action + '-unchecked');
            this.calculateApplyButtonAvailability();
        },
        selectAll: function() {
            this.$('.nodebox').addClass('node-to-' + this.action + '-checked').removeClass('node-to-' + this.action + '-unchecked');
            this.calculateApplyButtonAvailability();
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
                app.navbar.nodes.fetch();
            }, this));
        },
        getChosenNodes: function() {
            var chosenNodesIds = this.$('.node-to-' + this.action + '-checked').map(function() {return parseInt($(this).attr('data-node-id'), 10);}).get();
            var chosenNodes = this.availableNodes.filter(function(node) {return _.contains(chosenNodesIds, node.id);});
            return new models.Nodes(chosenNodes);
        },
        initialize: function(options) {
            this.tab = options.tab;
            this.role = options.role;
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
            this.$el.html(this.template({cluster: this.model, role: this.role, action: this.action}));
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
            this.tab = options.tab;
            this.role = options.role;
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
            this.tab = options.tab;
            this.role = options.role;
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
            this.tab.changeScreen(views.AddNodesScreen, {role: this.role});
        },
        deleteNodes: function() {
            this.tab.changeScreen(views.DeleteNodesScreen, {role: this.role});
        },
        initialize: function(options) {
            this.role = options.role;
            this.tab = options.tab;
        },
        render: function() {
            this.$el.html(this.template({nodes: this.collection, role: this.role}));
            if (this.collection.length) {
                var container = this.$('.node-list-container');
                this.collection.each(function(node) {
                    container.append(new views.Node({model: node, renameable: !this.collection.cluster.task('deploy', 'running')}).render().el);
                }, this);
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
            this.model.get('tasks').bind('remove', this.render, this);
        },
        render: function() {
            this.$el.html(this.template({cluster: this.model}));
            this.$('.verify-network').html((new views.NetworkTabVerification({model: this.model})).render().el);
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
                    this.model.fetch();
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
        collectData: function(parent_el,changed_data) {
            var model = this, param;
            _.each(parent_el.children().children('.wrapper'), function(el){
                if ($(el).data('nested')) {
                    param = $(el).find('legend:first').text();
                    changed_data[param] = {};
                    model.collectData($(el),changed_data[param]);
                } else {
                    param = $(el).find('input');
                    changed_data[param.attr('name')] = param.val();    
                }
            });
        },
        applyChanges: function() {
            var changed_data = {};
            this.collectData($('.settings-editable'),changed_data);
            this.settings.set({editable:changed_data});
            this.settings.save({}, {
                type: 'PUT',
                url: '/api/clusters/' + this.model.id + '/attributes'
            });
        },
        revertChanges: function() {
            $('.settings-editable')[0].reset();
        },
        setDefaults: function() {
            this.pasteSettings(this.settings.get('defaults'));
        },
        pasteSettings: function(settings) {
            _.each(_.keys(settings), function(el){
                var settingsGroupView = new views.SettingsGroup({legend: el, settings: settings[el]});
                this.$el.find('.settings-editable').append(settingsGroupView.render().el);
            }, this); 
            return this;
        },
        initialize: function() {
            this.settings = this.options.settings;
        },
        render: function() {
            this.$el.html(this.template({cluster: this.model}));
            this.pasteSettings(this.settings.get('editable'));
            return this;
        }
    });
    
    views.SettingsGroup = Backbone.View.extend({
        template: _.template(settingsGroupTemplate),
        events: {
            'change input': 'hasChanges'
        },
        hasChanges: function(el) {
            $('.btn-apply-changes').attr('disabled', false);
            $('.btn-revert-changes').attr('disabled', false);
            $(el.target).addClass('changed');
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

    return views;
});
