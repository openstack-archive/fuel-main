define(
[
    'models',
    'views/dialogs',
    'views/tasks',
    'text!templates/cluster/page.html',
    'text!templates/cluster/deployment_control.html',
    'text!templates/cluster/nodes_tab_summary.html',
    'text!templates/cluster/add_nodes_screen.html',
    'text!templates/cluster/node_list.html',
    'text!templates/cluster/node.html'
],
function(models, dialogViews, taskViews, clusterPageTemplate, deploymentControlTemplate, nodesTabSummaryTemplate, addNodesScreenTemplate, nodeListTemplate, nodeTemplate) {
    var views = {}

    views.ClusterPage = Backbone.View.extend({
        updateInterval: 5000,
        template: _.template(clusterPageTemplate),
        events: {
        },
        initialize: function(options) {
            _.defaults(this, options);
            this.model.bind('change', this.render, this);
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
            this.$el.html(this.template({cluster: this.model, tabs: this.tabs, activeTab: this.tab}));

            if (this.tab == 'nodes') {
                this.nodesTab = new views.NodesTab({model: this.model});
                this.$('#tab-' + this.tab).html(this.nodesTab.render().el);
            } else {
                this.$('#tab-' + this.tab).text('TBD');
            }

            return this;
        }
    });

    views.DeploymentControl = Backbone.View.extend({
        template: _.template(deploymentControlTemplate),
        events: {
            'click .apply-changes:not(.disabled)': 'applyChanges',
            'click .discard-changes:not(.disabled)': 'discardChanges'
        },
        applyChanges: function() {
            var task = new models.Task();
            task.save({}, {
                type: 'PUT',
                url: '/api/clusters/' + this.model.id + '/changes',
                success: _.bind(function() {
                    if (this.page == app.page) this.page.update();
                }, this)
            });
            this.disabled = true;
            this.render();
        },
        discardChanges: function() {
            var cluster = this.model;
            $.ajax({
                type: 'DELETE',
                url: '/api/clusters/' + this.model.id + '/changes',
                success: this.model.fetch,
                context: this.model
            });
            this.disabled = true;
            this.render();
        },
        initialize: function(options) {
            this.page = options.page;
            this.disabled = false;
            this.model.get('nodes').each(function(node) {
                node.bind('change:redeployment_needed', this.render, this);
            }, this);
        },
        render: function() {
            if (this.model.get('nodes').where({redeployment_needed: true}).length) {
                this.$el.html(this.template({disabled: this.disabled}));
            } else {
                this.$el.html('');
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
            this.$el.append((new views.NodesTabSummary({model: this.model, tab: this.tab})).render().el);
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

    views.AddNodesScreen = Backbone.View.extend({
        template: _.template(addNodesScreenTemplate),
        events: {
            'click .btn-discard': 'discardChanges',
            'click .btn-apply': 'applyChanges',
            'click .nodebox': 'toggleNode'
        },
        discardChanges: function() {
            this.tab.changeScreen(views.NodesByRolesScreen);
        },
        applyChanges: function(e) {
            if ($(e.currentTarget).attr('disabled')) return;
            this.$('.btn-apply').attr('disabled', true);
            var chosenNodesIds = this.$('.node-to-add-checked').map(function() {return parseInt($(this).attr('data-node-id'), 10)}).get();
            var chosenNodes = this.availableNodes.filter(function(node) {return _.contains(chosenNodesIds, node.id)});
            var chosenNodesCollection = new models.Nodes(chosenNodes);
            chosenNodesCollection.each(function(node) {
                node.set({
                    cluster_id: this.model.id,
                    role: this.role,
                    redeployment_needed: true
                });
            }, this);
            chosenNodesCollection.toJSON = function(options) {
                return this.map(function(node) {
                    return _.pick(node.attributes, 'id', 'cluster_id', 'role', 'redeployment_needed')
                });
            };
            Backbone.sync('update', chosenNodesCollection).done(_.bind(function() {
                this.tab.changeScreen(views.NodesByRolesScreen);
                this.model.fetch();
            }, this));
        },
        toggleNode: function(e) {
            $(e.currentTarget).toggleClass('node-to-add-checked').toggleClass('node-to-add-unchecked');
        },
        initialize: function(options) {
            this.tab = options.tab;
            this.role = options.role;
            this.availableNodes = new models.Nodes();
            this.availableNodes.deferred = this.availableNodes.fetch({data: {cluster_id: ''}});
        },
        render: function() {
            this.$el.html(this.template({cluster: this.model, role: this.role}));
            var nodesContainer = this.$('.available-nodes');
            this.availableNodes.deferred.done(_.bind(function() {
                if (this.availableNodes.length) {
                    nodesContainer.html('');
                    this.$('.btn-apply').attr('disabled', false);
                    this.availableNodes.each(function(node) {
                        nodesContainer.append(new views.Node({model: node, selectableForAddition: true}).render().el);
                    })
                } else {
                    nodesContainer.html('<div class="span12">No nodes available</div>');
                }
            }, this));
            return this;
        }
    });

    views.NodeList = Backbone.View.extend({
        template: _.template(nodeListTemplate),
        events: {
            'click .btn-add-nodes': 'addNodes'
        },
        addNodes: function() {
            this.tab.changeScreen(views.AddNodesScreen, {role: this.role});
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
            'click .node-name': 'startNameEditing',
            'keydown .node-name-editing': 'onNodeNameInputKeydown'
        },
        startNameEditing: function() {
            if (!this.renameable) return;
            if (this.model.collection.cluster.locked()) return;
            $('html').off(this.eventNamespace);
            $('html').on(this.eventNamespace, _.after(2, _.bind(function(e) {
                if (!$(e.target).closest(this.$el).length) {
                    this.endNameEditing();
                }
            }, this)));
            this.editingName = true;
            this.render();
            this.$('.node-name-editing input').focus();
        },
        endNameEditing: function() {
            $('html').off(this.eventNamespace);
            this.editingName = false;
            this.render();
        },
        onNodeNameInputKeydown: function(e) {
            if (e.which == 13) { // enter
                var input = this.$('.node-name-editing input');
                var name = input.attr('value');
                if (name != this.model.get('name')) {
                    input.attr('disabled', true).addClass('disabled');
                    this.model.update({name: name}, {complete: this.endNameEditing, context: this});
                } else {
                    this.endNameEditing();
                }
            } else if (e.which == 27) { // esc
                this.endNameEditing();
            }
        },
        initialize: function(options) {
            _.defaults(this, options);
            this.editingName = false;
            this.eventNamespace = 'click.editnodename' + this.model.id;
            this.model.bind('change', this.render, this);
        },
        render: function() {
            this.$el.html(this.template({
                node: this.model,
                editingName: this.editingName,
                selectableForAddition: this.selectableForAddition,
                selectableForDeletion: this.selectableForDeletion
            }));
            return this;
        }
    });

    return views;
});
