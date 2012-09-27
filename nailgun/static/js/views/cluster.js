define(
[
    'models',
    'views/dialogs',
    'views/tasks',
    'text!templates/cluster/page.html',
    'text!templates/cluster/nodes_tab_summary.html',
    'text!templates/cluster/edit_nodes_screen.html',
    'text!templates/cluster/node_list.html',
    'text!templates/cluster/node.html',
    'text!templates/cluster/network_tab_summary.html',
],
function(models, dialogViews, taskViews, clusterPageTemplate, nodesTabSummaryTemplate, editNodesScreenTemplate, nodeListTemplate, nodeTemplate, networkTabSummaryTemplate) {
    var views = {}

    views.ClusterPage = Backbone.View.extend({
        updateInterval: 5000,
        template: _.template(clusterPageTemplate),
        events: {
            'click .rename-cluster-btn': 'startClusterRenaming',
            'click .cluster-name-editable .discard-renaming-btn': 'endClusterRenaming',
            'click .cluster-name-editable .apply-name-btn': 'applyNewClusterName',
            'keydown .cluster-name-editable input': 'onClusterNameInputKeydown',
            'click .delete-cluster-btn': 'deleteCluster',
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
            var name = this.$('.cluster-name-editable input').val();
            if (name != this.model.get('name')) {
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
        deployCluster: function() {
            this.$('.deploy-btn').attr('disabled', true);
            $.ajax({
                type: 'PUT',
                url: '/api/clusters/' + this.model.id + '/changes'
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
            if (this.model.locked()) { // task is running
                _.delay(_.bind(this.update, this), this.updateInterval);
            }
        },
        update: function() {
            if (this == app.page) {
                this.model.fetch({
                    complete: _.bind(function() {
                        this.scheduleUpdate();
                    }, this)
                });
            }
        },
        render: function() {
            this.$el.html(this.template({
                cluster: this.model,
                tabs: this.tabs,
                activeTab: this.tab,
                renaming: this.renaming
            }));

            var tabContainer = this.$('#tab-' + this.tab);

            if (this.tab == 'nodes') {
                tabContainer.html(new views.NodesTab({model: this.model}).render().el);
            } else if (this.tab == 'network') {
                tabContainer.html(new views.NetworkTab({model: this.model}).render().el);
            }

            return this;
        }
    });

    views.NodesTab = Backbone.View.extend({
        changeScreen: function(newScreenView, screenOptions) {
            var options = _.extend({model: this.model, tab: this}, screenOptions || {});
            var screenView = new newScreenView(options);
            this.$el.html(screenView.render().el);
        },
        render: function() {
            this.$el.html('');
            this.changeScreen(views.NodesByRolesScreen);
            return this;
        }
    });

    views.NodesTabSummary = Backbone.View.extend({
        template: _.template(nodesTabSummaryTemplate),
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
                var nodes = this.model.get('nodes').filter(function(node) {return node.get('role') == role});
                var nodeListView = new views.NodeList({
                    collection: new models.Nodes(nodes),
                    role: role,
                    tab: this.tab
                });
                this.$el.append(nodeListView.render().el);
                if (index < roles.length - 1) this.$el.append('<hr>');
            }, this);
            return this;
        }
    });

    views.EditNodesScreen = Backbone.View.extend({
        template: _.template(editNodesScreenTemplate),
        events: {
            'click .btn-discard': 'discardChanges',
            'click .btn-apply:not([disabled])': 'applyChanges',
            'click .nodebox': 'toggleNode'
        },
        toggleNode: function(e) {
            $(e.currentTarget).toggleClass('node-to-' + this.action + '-checked').toggleClass('node-to-' + this.action + '-unchecked');
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
            }, this));
        },
        getChosenNodes: function() {
            var chosenNodesIds = this.$('.node-to-' + this.action + '-checked').map(function() {return parseInt($(this).attr('data-node-id'), 10)}).get();
            var chosenNodes = this.availableNodes.filter(function(node) {return _.contains(chosenNodesIds, node.id)});
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
                }, this)
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
                    return _.pick(node.attributes, 'id', 'cluster_id', 'role', 'redeployment_needed')
                });
            };
        }
    });

    views.DeleteNodesScreen = views.EditNodesScreen.extend({
        action: 'delete',
        initialize: function(options) {
            this.tab = options.tab;
            this.role = options.role;
            this.availableNodes = new models.Nodes(this.model.get('nodes').filter(function(node) {return node.get('role') == options.role}));
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
                    return _.pick(node.attributes, 'id', 'cluster_id', 'role', 'redeployment_needed')
                });
            };
        }
    });

    views.NodeList = Backbone.View.extend({
        template: _.template(nodeListTemplate),
        events: {
            'click .btn-add-nodes': 'addNodes',
            'click .btn-delete-nodes': 'deleteNodes'
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
                    container.append(new views.Node({model: node, renameable: true}).render().el);
                })
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
            if (!this.renameable || this.renaming) return;
            if (this.model.collection.cluster.locked()) return;
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
            var name = this.$('.node-name-editable input').val();
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
            'click .change-network-mode-btn': 'changeNetworkMode'
        },
        changeNetworkMode: function() {
            (new dialogViews.changeNetworkModeDialog({model: this.model})).render();
        },
        render: function() {
            this.$el.html(this.template({cluster: this.model}));
            return this;
        }
    });

    return views;
});
