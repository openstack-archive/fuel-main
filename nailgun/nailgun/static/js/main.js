// main router
var AppRouter = Backbone.Router.extend({
    routes: {
        ':hash': 'unknown',
        '': 'environment',
        'env/:id': 'environment'
    },
    environment: function(id) {
        if (this.environments) {
            this.environmentListView = new View.EnvironmentList({model: this.environments});
            $('#content').html(this.environmentListView.render().el);
        } else {
            this.environments = new Collection.Environment;
            this.environments.fetch({
                success: function() {
                    
                },
                error: function() {
                    $('#content').html("Error loading environments");
                }
            });
        }
    },
    unknown: function() {
        Backbone.history.navigate('', {replace: true});
    }
});

var View = {}

$(document).ready(function() {
    View.EnvironmentList = Backbone.View.extend({
        template: _.template($('#tpl-env-list').html()),
        render: function() {
            $(this.el).html(this.template({environments: this.model}));
            return this;
        }
    });
    
    window.app = new AppRouter();
    Backbone.history.start();
});
