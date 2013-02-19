define(
[
    'models',
    'views/common',
    'views/dialogs',
    'views/cluster_page_tabs/logs_tab',
    'text!templates/cluster/nodes_tab_summary.html',
    'text!templates/cluster/edit_nodes_screen.html',
    'text!templates/cluster/node_list.html',
    'text!templates/cluster/node.html'
],
function(models, commonViews, dialogViews, LogsTab, nodesTabSummaryTemplate, editNodesScreenTemplate, nodeListTemplate, nodeTemplate) {
    'use strict';
    var NodesTab, NodesByRolesScreen, EditNodesScreen, AddNodesScreen, DeleteNodesScreen, NodeList, Node;

    NodesTab = commonViews.Tab.extend({
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
            this.changeScreen(NodesByRolesScreen);
            return this;
        }
    });

    var NodesTabSummary = Backbone.View.extend({
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
        initialize: function(options) {
            this.model.bind('change:status', this.render, this);
        },
        render: function() {
            this.$el.html(this.template({cluster: this.model}));
            return this;
        }
    });

    NodesByRolesScreen = Backbone.View.extend({
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
            if (!task) {
                task = this.model.task('verify_networks', 'running');
            }
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
            var summary = new NodesTabSummary({model: this.model});
            this.registerSubView(summary);
            this.$el.append(summary.render().el);
            var roles = this.model.availableRoles();
            _.each(roles, function(role, index) {
                var nodes = new models.Nodes(this.model.get('nodes').where({role: role}));
                nodes.cluster = this.model;
                var nodeListView = new NodeList({
                    collection: nodes,
                    role: role,
                    tab: this.tab,
                    size: role == 'controller' ? this.model.get('mode') == 'ha' ? 0 : 1 : 0
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

    EditNodesScreen = Backbone.View.extend({
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
            if ($(e.target).closest(this.$('.node-hardware')).length) {return;}
            if (this.limit !== null && $(e.currentTarget).is('.node-to-' + this.action + '-unchecked') && this.$('.node-to-' + this.action + '-checked').length >= this.limit) {
                return;
            }
            $(e.currentTarget).toggleClass('node-to-' + this.action + '-checked').toggleClass('node-to-' + this.action + '-unchecked');
            this.calculateSelectAllTumblerState();
            this.calculateNotChosenNodesAvailability();
            this.calculateApplyButtonAvailability();
            app.forceWebkitRedraw(this.$('.nodebox'));
        },
        selectAll: function(e) {
            var checked = $(e.currentTarget).is(':checked');
            this.$('.nodebox').toggleClass('node-to-' + this.action + '-checked', checked).toggleClass('node-to-' + this.action + '-unchecked', !checked);
            this.calculateApplyButtonAvailability();
            app.forceWebkitRedraw(this.$('.nodebox'));
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
            this.$('.btn-apply').attr('disabled', !this.getChosenNodesIds().length);
        },
        discardChanges: function() {
            this.tab.changeScreen(NodesByRolesScreen);
        },
        applyChanges: function(e) {
            this.$('.btn-apply').attr('disabled', true);
            var nodes = new models.Nodes(this.getChosenNodes());
            this.modifyNodes(nodes);
            Backbone.sync('update', nodes).done(_.bind(function() {
                this.tab.changeScreen(NodesByRolesScreen);
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
            this.nodes.models = _.sortBy(this.nodes.models, function(node) {return node.get('mac');});
            if (this.nodes.length) {
                nodesContainer.html('');
                this.nodes.each(function(node) {
                    var options = {model: node};
                    if (this.action == 'add') {
                        options.selectableForAddition = true;
                    } else if (this.action == 'delete') {
                        options.selectableForDeletion = true;
                    }
                    var nodeView = new Node(options);
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

    AddNodesScreen = EditNodesScreen.extend({
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

    DeleteNodesScreen = EditNodesScreen.extend({
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

    NodeList = Backbone.View.extend({
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
            this.tab.changeScreen(AddNodesScreen, {role: this.role, limit: limit});
        },
        deleteNodes: function() {
            this.tab.changeScreen(DeleteNodesScreen, {role: this.role, limit: null});
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
            var placeholders;
            if (this.collection.cluster.get('mode') == 'ha' && this.role == 'controller') {
                placeholders = 3;
            } else {
                placeholders = this.size;
            }
            if (this.collection.length || placeholders) {
                var container = this.$('.node-list-container');
                this.collection.each(function(node) {
                    var nodeView = new Node({model: node, renameable: !this.collection.cluster.task('deploy', 'running')});
                    this.registerSubView(nodeView);
                    container.append(nodeView.render().el);
                }, this);
                if (nodesAfterDeployment.length < placeholders) {
                    _(placeholders - nodesAfterDeployment.length).times(function() {
                        container.append('<div class="span2 nodebox nodeplaceholder"></div>');
                    });
                }
            }
            return this;
        }
    });

    Node = Backbone.View.extend({
        template: _.template(nodeTemplate),
        events: {
            'click .node-name': 'startNodeRenaming',
            'keydown .node-renameable': 'onNodeNameInputKeydown',
            'click .node-hardware': 'showNodeInfo'
        },
        startNodeRenaming: function() {
            if (!this.renameable || this.renaming || this.model.collection.cluster.task('deploy', 'running')) {return;}
            $('html').off(this.eventNamespace);
            $('html').on(this.eventNamespace, _.after(2, _.bind(function(e) {
                if (!$(e.target).closest(this.$('.node-renameable input')).length) {
                    this.endNodeRenaming();
                }
            }, this)));
            this.renaming = true;
            this.render();
            this.$('.node-renameable input').focus();
        },
        endNodeRenaming: function() {
            $('html').off(this.eventNamespace);
            this.renaming = false;
            this.render();
        },
        applyNewNodeName: function() {
            var name = $.trim(this.$('.node-renameable input').val());
            if (name && name != this.model.get('name')) {
                this.$('.node-renameable input').attr('disabled', true);
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
        showNodeInfo: function() {
            var dialog = new dialogViews.ShowNodeInfoDialog({node: this.model});
            app.page.tab.registerSubView(dialog);
            dialog.render();
        },
        updateProgress: function() {
            var nodeStatus = this.model.get('status');
            if (this.model.get('status') == 'provisioning' || this.model.get('status') == 'deploying') {
                var progress = this.model.get('progress') || 0;
                this.$('.bar').css('width', (progress > 3 ? progress : 3) + '%');
            }
        },
        getLogsLink: function() {
            var status = this.model.get('status');
            var error = this.model.get('error_type');
            var options = {type: 'remote', node: this.model.id};
            if (status == 'discover') {
                options.source = 'bootstrap/messages';
            } else if (status == 'provisioning' || status == 'provisioned' || (status == 'error' && error == 'provision')) {
                options.source = 'install/anaconda';
            } else if (status == 'deploying' || status == 'ready' || (status == 'error' && error == 'deploy')) {
                options.source = 'install/puppet';
            }
            return '#cluster/' + app.page.model.id + '/logs/' + LogsTab.prototype.serializeOptions(options);
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
                selectableForDeletion: this.selectableForDeletion,
                logsLink: this.getLogsLink()
            }));
            this.updateProgress();
            return this;
        }
    });

    return NodesTab;
});
