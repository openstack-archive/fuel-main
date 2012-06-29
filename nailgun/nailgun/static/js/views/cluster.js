define(
[
    'models',
    'views/dialogs',
    'text!templates/cluster/page.html',
    'text!templates/cluster/node.html',
    'text!templates/cluster/deployment_control.html',
    'text!templates/cluster/role_chooser.html'
],
function(models, dialogViews, clusterPageTemplate, clusterNodeTemplate, deploymentControlTemplate, roleChooserTemplate) {
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
        render: function() {
            this.$el.html(this.template({cluster: this.model}));
            this.deploymentControl = new views.DeploymentControl({model: this.model});
            this.$('.deployment-control').html(this.deploymentControl.render().el);
            this.$('.node-list').html(new views.NodeList({model: this.model.get('nodes')}).render().el);
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
                success: _.bind(this.model.fetch, this.model)
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
            'click .roles > a': 'editRoles'
        },
        editRoles: function(e) {
            e.preventDefault();
            if (this.$('.node.off').length) return;
            if (this.$('.role-chooser').length) return;
            var roleChooser = (new views.NodeRoleChooser({model: this.model}));
            this.$('.roles').after(roleChooser.render().el);
        },
        initialize: function() {
            this.model.bind('change', this.render, this);
            this.model.bind('change:redeployment_needed', app.page.deploymentControl.render, app.page.deploymentControl);
        },
        render: function() {
            this.$el.html(this.template({node: this.model}));
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
