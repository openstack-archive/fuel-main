define(
[
    'models',
    'views/common',
    'views/cluster',
    'views/clusters',
    'views/release',
], function(models, commonViews, clusterViews, clustersViews, releaseViews) {
    var AppRouter = Backbone.Router.extend({
        routes: {
            'clusters': 'listClusters',
            'cluster/:id': 'showClusterInfo',
            'releases': 'listReleases',
            '*default': 'listClusters'
        },
        initialize: function() {
            this.navbar = new commonViews.Navbar({elements: [
                ['Clusters', '#clusters'],
                ['Available Releases', '#releases'],
            ]});
            $('#content').before(this.navbar.render().el);
            this.breadcrumb = new commonViews.Breadcrumb;
            $('#content').before(this.breadcrumb.render().el);
        },
        showClusterInfo: function(id) {
            if (this.clusters) {
                var cluster;
                if (id && (cluster = this.clusters.get(id))) {
                    this.navbar.setActive('clusters');
                    this.breadcrumb.setPath(['Home', '#'], ['Clusters', '#clusters'], cluster.get('name'));
                    this.page = new clusterViews.ClusterPage({model: cluster});
                    $('#content').html(this.page.render().el);
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
            this.navbar.setActive('clusters');
            this.breadcrumb.setPath(['Home', '#'], 'Clusters');

            if (this.clusters) {
                this.page = new clustersViews.ClustersPage({model: this.clusters});
                $('#content').html(this.page.render().el);
            } else {
                this.loadClusters(this.listClusters);
            }
        },
        listReleases: function() {
            this.navbar.setActive('releases');
            this.breadcrumb.setPath(['Home', '#'], 'Releases');

            if (this.releases) {
                this.page = new releaseViews.ReleasesPage({model: this.releases});
                $('#content').html(this.page.render().el);
            } else {
                this.releases = new models.Releases;
                this.releases.fetch({
                    success: _.bind(this.listReleases, this)
                });
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
