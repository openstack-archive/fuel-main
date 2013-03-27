define(
[
    'models',
    'views/common',
    'views/cluster_page',
    'views/cluster_page_tabs/nodes_tab',
    'views/clusters_page',
    'views/releases_page',
    'views/notifications_page',
    'views/support_page'
],
function(models, commonViews, ClusterPage, NodesTab, ClustersPage, ReleasesPage, NotificationsPage, SupportPage) {
    'use strict';

    var AppRouter = Backbone.Router.extend({
        routes: {
            'clusters': 'listClusters',
            'cluster/:id': 'showCluster',
            'cluster/:id/:tab(/:opt1)(/:opt2)': 'showClusterTab',
            'releases': 'listReleases',
            'notifications': 'showNotifications',
            'support': 'showSupportPage',
            '*default': 'listClusters'
        },
        initialize: function() {
            this.content = $('#content');
            this.navbar = new commonViews.Navbar({elements: [
                ['OpenStack Environments', '#clusters'],
                ['Support', '#support']
            ]});
            this.content.before(this.navbar.render().el);
            this.breadcrumbs = new commonViews.Breadcrumbs();
            this.content.before(this.breadcrumbs.render().el);
            this.footer = new commonViews.Footer();
            $('#footer').html(this.footer.render().el);
            this.content.find('.loading').addClass('layout-loaded');
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
        showClusterTab: function(id, activeTab) {
            if (!_.contains(ClusterPage.prototype.tabs, activeTab)) {
                this.showCluster(id);
                return;
            }

            var tabOptions = _.toArray(arguments).slice(2);

            if (activeTab == 'nodes') {
                // special case for nodes tab screen change
                try {
                    if (app.page.constructor == ClusterPage && app.page.model.id == id && app.page.tab.constructor == NodesTab) {
                        app.page.tab.tabOptions = tabOptions;
                        app.page.tab.routeScreen();
                        return;
                    }
                } catch(e) {}
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
                cluster.fetch().done(_.bind(render, this)).fail(_.bind(this.listClusters, this));
            }
        },
        listClusters: function() {
            this.navigate('#clusters', {replace: true});
            var clusters = new models.Clusters();
            clusters.fetch().done(_.bind(function() {
                this.setPage(new ClustersPage({collection: clusters}));
            }, this));
        },
        listReleases: function() {
            var releases = new models.Releases();
            releases.fetch().done(_.bind(function() {
                this.setPage(new ReleasesPage({collection: releases}));
            }, this));
        },
        showNotifications: function() {
            this.setPage(new NotificationsPage({notifications: app.navbar.notifications, nodes: app.navbar.nodes}));
        },
        showSupportPage: function() {
            this.setPage(new SupportPage());
        },
        serializeTabOptions: function(options) {
            return _.map(options, function(value, key) {
                return key + ':' + value;
            }).join(',');
        },
        deserializeTabOptions: function(serializedOptions) {
            return _.object(_.map(serializedOptions.split(','), function(option) {
                return option.split(':');
            }));
        },
        urlify: function (text) {
            var urlRegexp = /http:\/\/(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\//g;
            return text.replace(/\n/g, '<br/>').replace(urlRegexp, function(url) {
                return '<a target="_blank" href="' + url + '">' + url + '</a>';
            });
        },
        forceWebkitRedraw: function(el) {
            if (window.isWebkit) {
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
            // our server doesn't support PATCH, so use PUT instead
            var originalSync = Backbone.sync;
            Backbone.sync = function() {
                var args = arguments;
                if (args[0] == 'patch') {
                    args[0] = 'update';
                }
                return originalSync.apply(this, args);
            };

            window.isWebkit = navigator.userAgent.indexOf('AppleWebKit/') !== -1;

            var app = new AppRouter();
            window.app = app;

            Backbone.history.start();
        }
    };
});
