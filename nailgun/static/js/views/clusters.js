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
            this.tearDownRegisteredSubViews();
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
                this.timeout = _.delay(_.bind(this.update, this), this.updateInterval);
            }
        },
        update: function() {
            var deletionTask = this.model.task('cluster_deletion');
            var deploymentTask = this.model.task('deploy');
            if (deletionTask) {
                deletionTask.fetch()
                    .done(_.bind(this.scheduleUpdate, this))
                    .fail(_.bind(function(response) {
                        if (response.status == 404) {
                            this.model.collection.remove(this.model);
                            app.navbar.stats.nodes.fetch();
                            app.navbar.notifications.collection.fetch();
                        }
                    }, this));
            } else if (deploymentTask) {
                deploymentTask.fetch().done(_.bind(function() {
                    if (deploymentTask.get('status') == 'running') {
                        this.updateProgress();
                        this.scheduleUpdate();
                    } else {
                       this.model.fetch();
                    }
                }, this));
            }
        },
        updateProgress: function() {
            var task = this.model.task('deploy', 'running');
            if (task) {
                var progress = task.get('progress') || 0;
                this.$('.bar').css('width', (progress > 3 ? progress : 3) + '%');
            }
        },
        beforeTearDown: function() {
            if (this.timeout) {
                clearTimeout(this.timeout);
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
                    this.update();
                }
            }
            return this;
        }
    });

    return views;
});
