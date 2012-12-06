define(
[
    'models',
    'views/common',
    'views/dialogs',
    'text!templates/clusters/page.html',
    'text!templates/clusters/cluster.html',
    'text!templates/clusters/new.html'
],
function(models, commonViews, dialogViews, clustersPageTemplate, clusterTemplate, newClusterTemplate) {
    'use strict';

    var views = {};

    views.ClustersPage = commonViews.Page.extend({
        navbarActiveElement: 'clusters',
        breadcrumbsPath: [['Home', '#'], 'OpenStack Installations'],
        title: 'OpenStack Installations',
        template: _.template(clustersPageTemplate),
        render: function() {
            this.$el.html(this.template({clusters: this.collection}));
            var clustersView = new views.ClusterList({collection: this.collection});
            this.registerSubView(clustersView);
            this.$('.cluster-list').html(clustersView.render().el);
            return this;
        }
    });

    views.ClusterList = Backbone.View.extend({
        className: 'roles-block-row',
        newClusterTemplate: _.template(newClusterTemplate),
        events: {
            'click .create-cluster': 'createCluster'
        },
        createCluster: function() {
            var createClusterDialogView = new dialogViews.CreateClusterDialog({collection: this.collection});
            this.registerSubView(createClusterDialogView);
            createClusterDialogView.render();
        },
        initialize: function() {
            this.collection.bind('reset remove', this.render, this);
        },
        render: function() {
            this.$el.html('');
            this.collection.each(_.bind(function(cluster) {
                var clusterView = new views.Cluster({model: cluster});
                this.registerSubView(clusterView);
                this.$el.append(clusterView.render().el);
            }, this));
            this.$el.append(this.newClusterTemplate());
            return this;
        }
    });

    views.Cluster = Backbone.View.extend({
        tagName: 'a',
        className: 'span3 clusterbox',
        template: _.template(clusterTemplate),
        updateInterval: 3000,
        scheduleUpdate: function() {
            if (this.model.task('cluster_deletion', 'running') || this.model.task('deploy', 'running')) {
                _.delay(_.bind(this.update, this), this.updateInterval);
            } else {
                this.render();
            }
        },
        update: function() {
            var task = this.model.task('cluster_deletion');
            var cluster = this;
            if (task) {
                task.deferred = task.fetch({
                    error: function(model, response, options) {
                        if (response.status == 404) {
                            cluster.model.collection.remove(cluster.model);
                            app.navbar.stats.nodes.fetch();
                            app.navbar.notifications.collection.fetch();
                        }
                    }
                });
                task.deferred.done(_.bind(this.scheduleUpdate, this));
            } else {
                task = this.model.task('deploy');
                task.fetch().done(function() {
                    cluster.updateProgress();
                    cluster.scheduleUpdate();
                });
            }
        },
        updateProgress: function() {
            var task = this.model.task('deploy', 'running');
            if (task) {
                var progress = task.get('progress') || 0;
                var progressBar = this.$('.progress');
                progressBar.attr('data-original-title', 'Deployment in progress, ' + progress + '% completed').tooltip('fixTitle').tooltip();
                if (progressBar.is(':hover')) {
                    progressBar.tooltip('show');
                }
                this.$('.bar').css('width', (progress > 10 ? progress : 10) + '%');
            }
        },
        initialize: function() {
            this.model.bind('change', this.render, this);
        },
        render: function() {
            this.$el.html(this.template({cluster: this.model}));
            if (this.model.task('cluster_deletion', 'running')) {
                this.$el.addClass('disabled-cluster');
                this.update();
            } else {
                this.$el.attr('href', '#cluster/' + this.model.id + '/nodes');
                if (this.model.task('deploy', 'running')) {
                    this.$('.progress').tooltip('destroy');
                    this.update();
                }
            }
            return this;
        }
    });

    return views;
});
