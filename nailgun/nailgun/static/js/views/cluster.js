define(
[
    'models',
    'views/dialogs',
    'views/tasks',
    'text!templates/cluster/page.html',
    'text!templates/cluster/node.html',
    'text!templates/cluster/deployment_control.html',
    'text!templates/cluster/role_chooser.html'
],
function(models, dialogViews, taskViews, clusterPageTemplate, clusterNodeTemplate, deploymentControlTemplate, roleChooserTemplate) {
    var views = {}

    views.ClusterPage = Backbone.View.extend({
        className: 'span12',
        template: _.template(clusterPageTemplate),
        events: {
            'click .js-add-nodes': 'addRemoveNodes'
        },
        addRemoveNodes: function(e) {
            e.preventDefault();
            (new dialogViews.addRemoveNodesDialog({model: this.model})).render();
        },
        initialize: function() {
            this.model.bind('change', this.render, this);
        },
        renderTask: function() {
            if (this.model.get('task')) {
                this.$('.task-status').html(new taskViews.Task({model: this.model.get('task')}).render().el);
            }
        },
        render: function() {
            this.$el.html(this.template({cluster: this.model}));
            this.deploymentControl = new views.DeploymentControl({model: this.model});
            this.$('.deployment-control').html(this.deploymentControl.render().el);
            this.$('.node-list').html(new views.NodeList({model: this.model.get('nodes')}).render().el);
            this.renderTask();
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
                    if (task.get('status') == 'PENDING') {
                        this.model.fetch();
                    }
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
        initialize: function() {
            this.disabled = false;
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
        initialize: function() {
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
                this.$el.html('<div class="span12"><div class="alert">This cluster has no nodes</div></div>');
            }
            return this;
        }
    });

    views.Node = Backbone.View.extend({
        className: 'span3',
        template: _.template(clusterNodeTemplate),
        events: {
            'click .roles > a': 'editRoles',
            'click .node-name': 'startNameEditing',
            'keydown .node-name-editing': 'onNodeNameInputKeydown'
        },
        editRoles: function(e) {
            e.preventDefault();
            if (this.$('.node.off').length) return;
            if (this.$('.role-chooser').length) return;
            var roleChooser = (new views.NodeRoleChooser({model: this.model}));
            this.$('.roles').after(roleChooser.render().el);
        },
        startNameEditing: function(e) {
            e.preventDefault();
            $('html').off(this.eventNamespace);
            $('html').on(this.eventNamespace, _.bind(function(e) {
                if (this.handledFirstClick && !$(e.target).closest(this.$el).length) {
                    this.endNameEditing();
                } else {
                    this.handledFirstClick = true;
                }
            }, this));
            this.editingName = true;
            this.render();
            this.$('.node-name-editing input').focus();
        },
        endNameEditing: function() {
            $('html').off(this.eventNamespace);
            this.handledFirstClick = false;
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
        initialize: function() {
            this.editingName = false;
            this.handledFirstClick = false;
            this.eventNamespace = 'click.editnodename' + this.model.id;
            this.model.bind('change', this.render, this);
            this.model.bind('change:redeployment_needed', app.page.deploymentControl.render, app.page.deploymentControl);
        },
        render: function() {
            this.$el.html(this.template({node: this.model, editingName: this.editingName}));
            return this;
        }
    });

    views.NodeRoleChooser = Backbone.View.extend({
        tagName: 'ul',
        className: 'role-chooser',
        template: _.template(roleChooserTemplate),
        events: {
            'click .close': 'close',
            'click .role': 'toggleRole',
            'click .applybtn button:not(.disabled)': 'applyRoles'
        },
        close: function() {
            $('html').off(this.eventNamespace);
            this.remove();
        },
        toggleRole: function(e) {
            e.preventDefault();
            if ($(e.currentTarget).is('.unavailable')) return;
            $(e.currentTarget).toggleClass('checked').toggleClass('unchecked');
            if (_.isEqual(this.getChosenRoles(), this.originalRoles.pluck('id'))) {
                this.$('.applybtn button').addClass('disabled');
            } else {
                this.$('.applybtn button').removeClass('disabled');
            }
        },
        applyRoles: function() {
            var new_roles = this.getChosenRoles();
            var redeployment_needed = !_.isEqual(this.model.get('roles').pluck('id'), new_roles);
            this.model.update({new_roles: new_roles, redeployment_needed: redeployment_needed});
            this.close();
        },
        getChosenRoles: function() {
            return this.$('.role.checked').map(function() {return parseInt($(this).attr('data-role-id'), 10)}).get();
        },
        initialize: function() {
            this.handledFirstClick = false;
            this.originalRoles = this.model.get('redeployment_needed') ? this.model.get('new_roles') : this.model.get('roles');
            this.eventNamespace = 'click.chooseroles' + this.model.id;
            $('html').off(this.eventNamespace);
            $('html').on(this.eventNamespace, _.bind(function(e) {
                if (this.handledFirstClick && !$(e.target).closest(this.$el).length) {
                    this.close();
                } else {
                    this.handledFirstClick = true;
                }
            }, this));
            this.availableRoles = new models.Roles;
            this.availableRoles.fetch({
                data: {node_id: this.model.id},
                success: _.bind(this.render, this)
            });
        },
        render: function() {
            this.$el.html(this.template({availableRoles: this.availableRoles, nodeRoles: this.originalRoles}));
            return this;
        }
    });

    return views;
});
