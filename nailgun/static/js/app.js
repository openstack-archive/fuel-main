define(
[
    'models',
    'views/common',
    'views/cluster',
    'views/clusters',
    'views/release'
],
function(models, commonViews, clusterViews, clustersViews, releaseViews) {
    'use strict';

    var AppRouter = Backbone.Router.extend({
        routes: {
            'clusters': 'listClusters',
            'cluster/:id': 'showCluster',
            'cluster/:id/:tab': 'showClusterTab',
            'releases': 'listReleases',
            '*default': 'listClusters'
        },
        initialize: function() {
            this.content = $('#content');
            this.navbar = new commonViews.Navbar({elements: [
                ['OpenStack Installations', '#clusters'],
                ['Software Updates', '#releases']
            ]});
            this.content.before(this.navbar.render().el);
            this.breadcrumb = new commonViews.Breadcrumb();
            this.content.before(this.breadcrumb.render().el);
        },
        setPage: function(newPage) {
            if (this.page) {
                this.page.tearDown();
            }
            this.page = newPage;
            this.content.html(this.page.render().el);
        },
        showCluster: function(id) {
            this.navigate('#cluster/' + id + '/nodes', {trigger: true, replace: true});
        },
        showClusterTab: function(id, activeTab) {
            var tabs = ['nodes', 'network', 'settings', 'actions', 'logs'];
            if (!_.contains(tabs, activeTab)) {
                this.showCluster(id);
                return;
            }

            var cluster;
            var render = function() {
                this.navbar.setActive('clusters');
                this.breadcrumb.setPath(['Home', '#'], ['OpenStack Installations', '#clusters'], cluster.get('name'));
                this.setPage(new clusterViews.ClusterPage({model: cluster, tabs: tabs, activeTab: activeTab}));
            };

            if (app.page && app.page.constructor == clusterViews.ClusterPage && app.page.model.id == id) {
                // just another tab has been chosen, do not load cluster again
                cluster = app.page.model;
                render.call(this);
            } else {
                cluster = new models.Cluster({id: id});
                cluster.fetch({
                    success: _.bind(render, this),
                    error: _.bind(this.listClusters, this)
                });
            }
        },
        listClusters: function() {
            this.navigate('#clusters', {replace: true});
            var clusters = new models.Clusters();
            clusters.fetch({
                success: _.bind(function() {
                    this.navbar.setActive('clusters');
                    this.breadcrumb.setPath(['Home', '#'], 'OpenStack Installations');
                    this.setPage(new clustersViews.ClustersPage({collection: clusters}));
                }, this)
            });
        },
        listReleases: function() {
            var releases = new models.Releases();
            releases.fetch({
                success: _.bind(function() {
                    this.navbar.setActive('releases');
                    this.breadcrumb.setPath(['Home', '#'], 'Software Updates');
                    this.setPage(new releaseViews.ReleasesPage({collection: releases}));
                }, this)
            });
        }
    });

    return {
        initialize: function() {
            var app = new AppRouter();
            window.app = app;
            Backbone.history.start();

            // tooltips
            $('body').tooltip({selector: "[rel=tooltip]"});
            app.bind('all', function(route) {$('.tooltip').remove();});
        }
    };
});
