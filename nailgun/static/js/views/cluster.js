define(
[
    'models',
    'views/dialogs',
    'views/tasks',
    'text!templates/cluster/page.html',
    'text!templates/cluster/deployment_control.html',
    'text!templates/cluster/tab.html',
    'text!templates/cluster/nodes_tab_summary.html',
    'text!templates/cluster/node_list.html',
    'text!templates/cluster/node.html'
],
function(models, dialogViews, taskViews, clusterPageTemplate, deploymentControlTemplate, tabTemplate, nodesTabSummaryTemplate, nodeListTemplate, nodeTemplate) {
    var views = {}

    views.ClusterPage = Backbone.View.extend({
        updateInterval: 5000,
        template: _.template(clusterPageTemplate),
        events: {
            'click .add-nodes-btn': 'addRemoveNodes',
            'click .assign-roles-btn': 'assignRoles'
        },
        addRemoveNodes: function(e) {
            (new dialogViews.addRemoveNodesDialog({model: this.model})).render();
        },
        assignRoles: function(e) {
            (new dialogViews.assignRolesDialog({model: this.model})).render();
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
        template: _.template(tabTemplate),
        className: 'roles-block-row',
        render: function() {
            this.$el.html(this.template());
            this.content = new views.NodesTabContent({model: this.model});
            this.summary = new views.NodesTabSummary({model: this.model});
            this.$('.tab-content').html(this.content.render().el);
            this.$('.tab-summary').html(this.summary.render().el);
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

    views.NodesTabContent = Backbone.View.extend({
        initialize: function(options) {
            this.model.get('nodes').bind('reset', this.render, this);
            this.model.get('nodes').bind('add', this.render, this);
        },
        render: function() {
            this.$el.html('');
            var roles = this.model.availableRoles();
            _.each(roles, function(role, index) {
                var nodes = this.model.get('nodes').filter(function(node) {return node.get('role') == role});
                this.$el.append((new views.NodeList({collection: new models.Nodes(nodes), role: role})).render().el);
                if (index < roles.length - 1) this.$el.append('<hr>');
            }, this);
            return this;
        }
    });

    views.NodeList = Backbone.View.extend({
        template: _.template(nodeListTemplate),
        initialize: function(options) {
            this.role = options.role;
        },
        render: function() {
            this.$el.html(this.template({nodes: this.collection, role: this.role}));
            if (this.collection.length) {
                var container = this.$('.node-list-container');
                this.collection.each(function(node) {
                    container.append(new views.Node({model: node}).render().el);
                })
            }
            return this;
        }
    });

    views.Node = Backbone.View.extend({
        className: 'span3',
        template: _.template(nodeTemplate),
        events: {
            'click .node-name': 'startNameEditing',
            'keydown .node-name-editing': 'onNodeNameInputKeydown'
        },
        startNameEditing: function() {
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
            this.editingName = false;
            this.eventNamespace = 'click.editnodename' + this.model.id;
            this.model.bind('change', this.render, this);
        },
        render: function() {
            this.$el.html(this.template({node: this.model, editingName: this.editingName}));
            return this;
        }
    });

    return views;
});
