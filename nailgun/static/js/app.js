/*
 * Copyright 2013 Mirantis, Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use this file except in compliance with the License. You may obtain
 * a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations
 * under the License.
**/
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
                ['Environments', '#clusters'],
                ['Releases', '#releases'],
                ['Support', '#support']
            ]});
            this.content.before(this.navbar.render().el);
            this.breadcrumbs = new commonViews.Breadcrumbs();
            this.content.before(this.breadcrumbs.render().el);
            this.footer = new commonViews.Footer();
            $('#footer').html(this.footer.render().el);
            this.content.find('.loading').addClass('layout-loaded');
        },
        setPage: function(NewPage, options) {
            if (this.page) {
                this.page.tearDown();
            }
            this.page = new NewPage(options);
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
                        app.page.tab.routeScreen(tabOptions);
                        return;
                    }
                } catch(e) {}
            }

            var cluster, tasks;
            var render = function() {
                this.setPage(ClusterPage, {
                    model: cluster,
                    activeTab: activeTab,
                    tabOptions: tabOptions,
                    tasks: tasks
                });
            };

            if (app.page && app.page.constructor == ClusterPage && app.page.model.id == id) {
                // just another tab has been chosen, do not load cluster again
                cluster = app.page.model;
                tasks = app.page.tasks;
                render.call(this);
            } else {
                cluster = new models.Cluster({id: id});
                tasks = new models.Tasks();
                tasks.fetch = function(options) {
                    return this.constructor.__super__.fetch.call(this, _.extend({data: {cluster_id: ''}}, options));
                };
                $.when(cluster.fetch(), cluster.fetchRelated('nodes'), cluster.fetchRelated('tasks'), tasks.fetch())
                    .done(_.bind(render, this))
                    .fail(_.bind(this.listClusters, this));
            }
        },
        listClusters: function() {
            this.navigate('#clusters', {replace: true});
            var clusters = new models.Clusters();
            var nodes = new models.Nodes();
            var tasks = new models.Tasks();
            $.when(clusters.fetch(), nodes.fetch(), tasks.fetch()).done(_.bind(function() {
                clusters.each(function(cluster) {
                    cluster.set('nodes', new models.Nodes(nodes.where({cluster: cluster.id})));
                    cluster.set('tasks', new models.Tasks(tasks.where({cluster: cluster.id})));
                }, this);
                this.setPage(ClustersPage, {collection: clusters});
            }, this));
        },
        listReleases: function() {
            var releases = new models.Releases();
            var tasks = new models.Tasks();
            tasks.fetch = function(options) {
                return this.constructor.__super__.fetch.call(this, _.extend({data: {cluster_id: ''}}, options));
            };
            $.when(releases.fetch(), tasks.fetch()).done(_.bind(function() {
                this.setPage(ReleasesPage, {
                    collection: releases,
                    tasks: tasks
                });
            }, this));
        },
        showNotifications: function() {
            this.setPage(NotificationsPage, {notifications: app.navbar.notifications, nodes: app.navbar.nodes});
        },
        showSupportPage: function() {
            this.setPage(SupportPage);
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
