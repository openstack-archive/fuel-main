define(
[
    'models',
    'views/dialogs',
    'views/tasks',
    'text!templates/cluster/page.html',
    'text!templates/cluster/deployment_control.html',
    'text!templates/cluster/tab.html',
    'text!templates/cluster/nodes_tab_summary.html',
    'text!templates/cluster/node.html',
],
function(models, dialogViews, taskViews, clusterPageTemplate, deploymentControlTemplate, tabTemplate, nodesTabSummary, nodeTemplate) {
    var views = {}

    views.ClusterPage = Backbone.View.extend({
        className: 'span12',
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
        className: 'row-fluid',
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
        template: _.template(nodesTabSummary),
        render: function() {
            this.$el.html(this.template({cluster: this.model}));
            return this;
        }
    });

    views.NodesTabContent = Backbone.View.extend({
        render: function() {
            this.$el.html((new views.NodeList({collection: this.model.get('nodes')})).render().el);
            return this;
        }
    });

    views.NodeList = Backbone.View.extend({
        className: 'row-fluid',
        initialize: function(options) {
            this.collection.bind('reset', this.render, this);
            this.collection.bind('add', this.render, this);
        },
        render: function() {
            if (this.collection.length) {
                this.$el.html('');
                this.collection.each(_.bind(function(node) {
                    this.$el.append(new views.Node({model: node}).render().el);
                }, this));
            } else {
                this.$el.html('<div class="span12"><div class="alert">There are no nodes of this type</div></div>');
            }
            return this;
        }
    });

    views.Node = Backbone.View.extend({
        className: 'span4',
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
