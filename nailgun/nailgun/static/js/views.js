define(
    [
        'text!jst/env.html',
        'text!jst/env_list.html',
        'text!jst/node.html'
    ],
    function(envTemplate, envListTemplate, nodeTemplate) {
    var views = {}

    views.Environment = Backbone.View.extend({
        tagName: 'span',
        template: _.template(envTemplate),
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
                        container.html('This environment has no nodes');
                    }
                }
            }, this);
        },
        render: function() {
            this.$el.html(this.template({environment: this.model}));
            return this;
        }
    });

    views.EnvironmentList = Backbone.View.extend({
        template: _.template(envListTemplate),
        events: {
            'click #add': 'addEnvironment'
        },
        addEnvironment: function() {
            alert('TBD')
        },
        initialize: function() {
            this.model.bind('reset', this.render, this);
            this.model.bind('add', this.render, this);
        },
        render: function() {
            this.$el.html(this.template({environments: this.model}));

            var environments = [];
            this.model.each(function(environment) {
                environments.push(new views.Environment({model: environment}).render().el);
            });
            $('#env-list').prepend(environments);

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
