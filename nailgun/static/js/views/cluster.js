define(
[
    'models',
    'views/dialogs',
    'views/tasks',
    'text!templates/cluster/page.html',
    'text!templates/cluster/node.html',
    'text!templates/cluster/deployment_control.html',
],
function(models, dialogViews, taskViews, clusterPageTemplate, clusterNodeTemplate, deploymentControlTemplate) {
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
        initialize: function() {
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
            this.$el.html(this.template({cluster: this.model}));
            this.deploymentControl = new views.DeploymentControl({model: this.model, page: this});
            this.$('.deployment-control').html(this.deploymentControl.render().el);
            this.nodeList = new views.NodeList({model: this.model.get('nodes')});
            this.$('.node-list').html(this.nodeList.render().el);
            if (this.model.get('task')) {
                this.task = new taskViews.Task({model: this.model.get('task'), page: this});
                this.$('.task-status').html(this.task.render().el);
            } else {
                this.task = null;
                this.$('.task-status').html('');
            }
            if (this.model.locked()) {
                this.$el.addClass('cluster-locked').removeClass('cluster-editable');
                this.$('.cluster-control button').addClass('disabled').attr('disabled', true);
            } else {
                this.$el.addClass('cluster-editable').removeClass('cluster-locked');
                this.$('.cluster-control button').removeClass('disabled').attr('disabled', false);
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

    views.NodeList = Backbone.View.extend({
        className: 'row',
        initialize: function(options) {
            this.model.bind('reset', this.render, this);
            this.model.bind('add', this.render, this);
        },
        render: function() {
            if (this.model.length) {
                this.$el.html('');
                this.model.each(_.bind(function(node) {
                    this.$el.append(new views.Node({model: node}).render().el);
                }, this));
            } else {
                this.$el.html('<div class="span12"><div class="alert">This OpenStack installation does not have any nodes</div></div>');
            }
            return this;
        }
    });

    views.Node = Backbone.View.extend({
        className: 'span3',
        template: _.template(clusterNodeTemplate),
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
