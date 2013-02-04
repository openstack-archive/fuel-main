define(
[
    'models',
    'views/common',
    'views/cluster_page',
    'views/clusters_page',
    'views/releases_page',
    'views/notifications_page'
],
function(models, commonViews, ClusterPage, ClustersPage, ReleasesPage, NotificationsPage) {
    'use strict';

    var AppRouter = Backbone.Router.extend({
        routes: {
            'clusters': 'listClusters',
            'cluster/:id': 'showCluster',
            'cluster/:id/:tab': 'showClusterTab',
            'cluster/:id/:tab/*options': 'showClusterTab',
            'releases': 'listReleases',
            'notifications': 'showNotifications',
            '*default': 'listClusters'
        },
        initialize: function() {
            this.content = $('#content');
            this.navbar = new commonViews.Navbar({elements: [
                ['OpenStack Installations', '#clusters'],
                ['OpenStack Releases', '#releases']
            ]});
            this.content.before(this.navbar.render().el);
            this.breadcrumbs = new commonViews.Breadcrumbs();
            this.content.before(this.breadcrumbs.render().el);
        },
        setPage: function(newPage) {
            if (this.page) {
                this.page.tearDown();
            }
            this.page = newPage;
            this.page.updateNavbar();
            this.page.updateBreadcrumbs();
            this.page.updateTitle();
            this.content.html(this.page.render().el);
        },
        showCluster: function(id) {
            this.navigate('#cluster/' + id + '/nodes', {trigger: true, replace: true});
        },
        showClusterTab: function(id, activeTab, tabOptions) {
            if (!_.contains(ClusterPage.prototype.tabs, activeTab)) {
                this.showCluster(id);
                return;
            }

            var cluster;
            var render = function() {
                this.setPage(new ClusterPage({model: cluster, activeTab: activeTab, tabOptions: tabOptions}));
            };

            if (app.page && app.page.constructor == ClusterPage && app.page.model.id == id) {
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
                    this.setPage(new ClustersPage({collection: clusters}));
                }, this)
            });
        },
        listReleases: function() {
            var releases = new models.Releases();
            releases.fetch({
                success: _.bind(function() {
                    this.setPage(new ReleasesPage({collection: releases}));
                }, this)
            });
        },
        showNotifications: function() {
            this.setPage(new NotificationsPage({collection: app.navbar.notifications, nodes: app.navbar.stats.nodes}));
        },
        urlify: function (text) {
            var urlRegexp = /http:(\&\#x2F\;){2}(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])(\&\#x2F\;)/g;
            return text.replace(/\n/g, '<br/>').replace(urlRegexp, function(url) {
                return '<a target="_blank" href="' + url + '">' + url + '</a>';
            });
        },
        forceWebkitRedraw: function(el) {
            if ($.browser.webkit) {
                el.each(function() {
                    this.style.webkitTransform = 'scale(1)';
                    var dummy = this.offsetHeight;
                    this.style.webkitTransform = '';
                });
            }
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
