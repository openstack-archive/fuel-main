define(
[
    'views/dialogs',
    'text!templates/cluster/list.html',
    'text!templates/cluster/info.html',
    'text!templates/cluster/node.html',
    'text!templates/cluster/role_chooser.html'
],
function(dialogViews, clusterListTemplate, clusterInfoTemplate, clusterNodeTemplate, roleChooserTemplate) {
    var views = {}

    views.Info = Backbone.View.extend({
        className: 'span12',
        template: _.template(clusterInfoTemplate),
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
            this.$('.node_list').html(new views.NodeList({model: this.model.get('nodes')}).render().el);
            return this;
        }
    });

    views.List = Backbone.View.extend({
        className: 'span12',
        template: _.template(clusterListTemplate),
        events: {
            'click .js-create-cluster': 'createCluster'
        },
        createCluster: function(e) {
            e.preventDefault();
            (new dialogViews.createClusterDialog()).render();
        },
        initialize: function() {
            this.model.bind('reset', this.render, this);
            this.model.bind('add', this.render, this);
        },
        render: function() {
            this.$el.html(this.template({clusters: this.model}));
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
        },
        render: function() {
            this.$el.html(this.template({node: this.model}));
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

    views.NodeRoleChooser = Backbone.View.extend({
        tagName: 'ul',
        className: 'role-chooser',
        template: _.template(roleChooserTemplate),
        events: {
            'click .close': 'close'
        },
        close: function() {
            $('html').off(this.eventNamespace);
            this.remove();
        },
        initialize: function() {
            this.handledFirstClick = false;
            this.eventNamespace = 'click.chooseroles' + this.model.id;
        },
        render: function() {
            this.$el.html(this.template({roles: this.model.get('roles')}));
            $('html').on(this.eventNamespace, _.bind(function(e) {
                if (this.handledFirstClick && !$(e.target).closest(this.$el).length) {
                    this.close();
                } else {
                    this.handledFirstClick = true;
                }
            }, this));
            return this;
        }
    });

    return views;
});
