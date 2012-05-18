// main router
var AppRouter = Backbone.Router.extend({
    routes: {
        ':hash': 'unknown',
        '': 'environment',
        'env/:id': 'environment'
    },
    environment: function(id) {
        if (this.environments) {
            var activeEnvironment = this.environments.where({active: true})[0]
            if (activeEnvironment) {
                activeEnvironment.set('active', false);
            }
            
            if (id && this.environments.get(id)) {
                this.environments.get(id).set('active', true);
            } else {
                this.environments.at(0).set('active', true)
            }
        } else {
            this.environments = new Collection.Environment;
            this.environmentListView = new View.EnvironmentList({
                model: this.environments,
                el: $('#content')
            });
            this.environments.fetch({
                success: _.bind(function() {
                    this.environment(id);
                }, this),
                error: function() {
                    $('#content').html("Error loading environments");
                }
            });
        }
    },
    unknown: function() {
        Backbone.history.navigate('', {replace: true, trigger: true});
    }
});

var View = {}

$(document).ready(function() {
    View.Environment = Backbone.View.extend({
        tagName: 'span',
        template: _.template($('#tpl_env').html()),
        initialize: function() {
            this.model.bind('change:active', function() {
                this.render();
                
                var container = $('#nodes');
                
                if (this.model.get('active')) {
                    if (this.model.get('nodes').length) {
                        new View.NodeList({
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
    
    View.EnvironmentList = Backbone.View.extend({
        template: _.template($('#tpl_env_list').html()),
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
                environments.push(new View.Environment({model: environment}).render().el);
            });
            $('#env-list').prepend(environments);
            
            return this;
        }
    });
    
    View.Node = Backbone.View.extend({
        tagName: 'li',
        className: 'node',
        template: _.template($('#tpl_node').html()),
        initialize: function() {
            this.model.bind('change', this.render, this);
        },
        render: function() {
            this.$el.addClass(this.model.get('status'));
            this.$el.html(this.template({node: this.model}));
            return this;
        }
    });
    
    View.NodeList = Backbone.View.extend({
        render: function() {
            this.$el.html('');
            this.model.each(_.bind(function(node) {
                this.$el.append(new View.Node({model: node}).render().el);
            }, this));
            
            return this;
        }
    });
    
    window.app = new AppRouter();
    Backbone.history.start();
});
