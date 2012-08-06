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
                ['OpenStack Installations', '#clusters'],
                ['Software Updates', '#releases'],
            ]});
            $('#content').before(this.navbar.render().el);
            this.breadcrumb = new commonViews.Breadcrumb;
            $('#content').before(this.breadcrumb.render().el);
        },
        showClusterInfo: function(id) {
            var cluster = new models.Cluster({id: id});
            cluster.fetch({
                success: _.bind(function() {
                    this.navbar.setActive('clusters');
                    this.breadcrumb.setPath(['Home', '#'], ['OpenStack Installations', '#clusters'], cluster.get('name'));
                    this.page = new clusterViews.ClusterPage({model: cluster});
                    $('#content').html(this.page.render().el);
                }, this),
                error: _.bind(function() {
                    this.listClusters();
                }, this)
            });
        },
        listClusters: function() {
            this.navigate('#clusters', {replace: true});
            var clusters = new models.Clusters;
            clusters.fetch({
                success: _.bind(function() {
                    this.navbar.setActive('clusters');
                    this.breadcrumb.setPath(['Home', '#'], 'OpenStack Installations');
                    this.page = new clustersViews.ClustersPage({model: clusters});
                    $('#content').html(this.page.render().el);
                }, this)
            });
        },
        listReleases: function() {
            var releases = new models.Releases;
            releases.fetch({
                success: _.bind(function() {
                    this.navbar.setActive('releases');
                    this.breadcrumb.setPath(['Home', '#'], 'Software Updates');
                    this.page = new releaseViews.ReleasesPage({model: releases});
                    $('#content').html(this.page.render().el);
                }, this)
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
