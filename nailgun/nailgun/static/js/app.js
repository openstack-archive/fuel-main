define(['models', 'views'], function(models, views) {
    var AppRouter = Backbone.Router.extend({
        routes: {
            'clusters': 'listClusters',
            'cluster/:id': 'showClusterInfo',
            '*default': 'listClusters'
        },
        initialize: function() {
            this.breadcrumb = new views.Breadcrumb;
            $('#content').before(this.breadcrumb.render().el);
        },
        showClusterInfo: function(id) {
            if (this.clusters) {
                var cluster;
                if (id && (cluster = this.clusters.get(id))) {
                    this.breadcrumb.setPath(['Home', '#'], ['Clusters', '#clusters'], cluster.get('name'));
                    $('#content').html(new views.ClusterInfo({model: cluster}).render().el);
                } else {
                    this.listClusters();
                }
            } else {
                this.loadClusters(function() {
                    this.showClusterInfo(id);
                });
            }
        },
        listClusters: function() {
            this.navigate('#clusters', {replace: true});
            this.breadcrumb.setPath(['Home', '#'], 'Clusters');

            if (this.clusters) {
                $('#content').html(new views.ClusterList({model: this.clusters}).render().el);
            } else {
                this.loadClusters(this.listClusters);
            }
        },
        loadClusters: function(callback) {
            this.clusters = new models.Clusters;
            this.clusters.fetch({
                success: _.bind(callback, this)
            });
        }
    });

    return {
        initialize: function() {
            window.app = new AppRouter();
            Backbone.history.start();
        }
    };
});
