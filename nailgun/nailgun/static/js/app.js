define(['models', 'views'], function(models, views) {
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
                this.environments = new models.Environments;
                this.environmentListView = new views.EnvironmentList({
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

    return {
        initialize: function() {
            window.app = new AppRouter();
            Backbone.history.start();
        }
    };
});
