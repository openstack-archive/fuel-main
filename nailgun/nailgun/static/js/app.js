define(['models', 'views'], function(models, views) {
    var AppRouter = Backbone.Router.extend({
        routes: {
            ':hash': 'unknown',
            '': 'cluster',
            'cluster/:id': 'cluster'
        },
        cluster: function(id) {
            if (this.clusters) {
                var activeCluster = this.clusters.where({active: true})[0]
                if (activeCluster) {
                    activeCluster.set('active', false);
                }
                if (id && this.clusters.get(id)) {
                    this.clusters.get(id).set('active', true);
                } else {
                    this.clusters.at(0).set('active', true)
                }
            } else {
                this.clusters = new models.Clusters;
                this.clusterListView = new views.ClusterList({
                    model: this.clusters,
                    el: $('#content')
                });
                this.clusters.fetch({
                    success: _.bind(function() {
                        this.cluster(id);
                    }, this),
                    error: function() {
                        $('#content').html("Error loading clusters");
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
