define(
    [
        'text!jst/cluster.html',
        'text!jst/cluster_list.html',
        'text!jst/node.html'
    ],
    function(clusterTemplate, clusterListTemplate, nodeTemplate) {
    var views = {}

    views.Cluster = Backbone.View.extend({
        tagName: 'span',
        template: _.template(clusterTemplate),
        initialize: function() {
            this.model.bind('change:active', function() {
                this.render();

                var container = $('#nodes');

                if (this.model.get('active')) {
                    if (this.model.get('nodes').length) {
                        new views.NodeList({
                            model: this.model.get('nodes'),
                            el: container
                        }).render();
                    } else {
                        container.html('This cluster has no nodes');
                    }
                }
            }, this);
        },
        render: function() {
            this.$el.html(this.template({cluster: this.model}));
            return this;
        }
    });

    views.ClusterList = Backbone.View.extend({
        template: _.template(clusterListTemplate),
        events: {
            'click #add': 'addCluster'
        },
        addCluster: function() {
            alert('TBD')
        },
        initialize: function() {
            this.model.bind('reset', this.render, this);
            this.model.bind('add', this.render, this);
        },
        render: function() {
            this.$el.html(this.template({clusters: this.model}));

            var clusters = [];
            this.model.each(function(cluster) {
                clusters.push(new views.Cluster({model: cluster}).render().el);
            });
            $('#cluster-list').prepend(clusters);

            return this;
        }
    });

    views.Node = Backbone.View.extend({
        tagName: 'li',
        className: 'node',
        template: _.template(nodeTemplate),
        initialize: function() {
            this.model.bind('change', this.render, this);
        },
        render: function() {
            this.$el.addClass(this.model.get('status'));
            this.$el.html(this.template({node: this.model}));
            if (this.model.get('roles').length) {
                this.$el.append(new views.RoleList({
                    model: this.model.get('roles')
                }).render().el);
            }
            return this;
        }
    });

    views.NodeList = Backbone.View.extend({
        render: function() {
            this.$el.html('');
            this.model.each(_.bind(function(node) {
                this.$el.append(new views.Node({model: node}).render().el);
            }, this));
            return this;
        }
    });

    views.Role = Backbone.View.extend({
        tagName: 'li',
        initialize: function() {
            this.model.bind('change', this.render, this);
        },
        render: function() {
            this.$el.addClass(this.model.id);
            this.$el.text(this.model.get('name'));
            return this;
        }
    });

    views.RoleList = Backbone.View.extend({
        tagName: 'ul',
        className: 'roles',
        initialize: function() {
            this.model.bind('change', this.render, this);
            this.model.bind('add', this.render, this);
        },
        render: function() {
            this.$el.html('');
            this.model.each(_.bind(function(role) {
                this.$el.append(new views.Role({model: role}).render().el);
            }, this));
            return this;
        }
    });

    return views;
});
