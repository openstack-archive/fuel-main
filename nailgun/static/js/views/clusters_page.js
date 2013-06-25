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
    var ClustersPage, ClusterList, Cluster;

    ClustersPage = commonViews.Page.extend({
        navbarActiveElement: 'clusters',
        breadcrumbsPath: [['Home', '#'], 'Environments'],
        title: 'Environments',
        template: _.template(clustersPageTemplate),
        render: function() {
            this.$el.html(this.template({clusters: this.collection}));
            var clustersView = new ClusterList({collection: this.collection});
            this.registerSubView(clustersView);
            this.$('.cluster-list').html(clustersView.render().el);
            return this;
        }
    });

    ClusterList = Backbone.View.extend({
        className: 'roles-block-row',
        newClusterTemplate: _.template(newClusterTemplate),
        events: {
            'click .create-cluster': 'createCluster'
        },
        createCluster: function() {
            var createClusterDialogView = new dialogViews.CreateClusterDialog({collection: this.collection});
            app.page.registerSubView(createClusterDialogView);
            createClusterDialogView.render();
        },
        initialize: function() {
            this.collection.on('sync add', this.render, this);
        },
        render: function() {
            this.tearDownRegisteredSubViews();
            this.$el.html('');
            this.collection.each(_.bind(function(cluster) {
                var clusterView = new Cluster({model: cluster});
                this.registerSubView(clusterView);
                this.$el.append(clusterView.render().el);
            }, this));
            this.$el.append(this.newClusterTemplate());
            return this;
        }
    });

    Cluster = Backbone.View.extend({
        tagName: 'a',
        className: 'span3 clusterbox',
        template: _.template(clusterTemplate),
        updateInterval: 3000,
        scheduleUpdate: function() {
            if (this.model.task('cluster_deletion', ['running', 'ready']) || this.model.task('deploy', 'running')) {
                this.registerDeferred($.timeout(this.updateInterval).done(_.bind(this.update, this)));
            }
        },
        update: function() {
            var deletionTask = this.model.task('cluster_deletion');
            var deploymentTask = this.model.task('deploy');
            var request;
            if (deletionTask) {
                request = deletionTask.fetch();
                request.done(_.bind(this.scheduleUpdate, this));
                request.fail(_.bind(function(response) {
                    if (response.status == 404) {
                        this.model.collection.remove(this.model);
                        this.remove();
                        app.navbar.refresh();
                    }
                }, this));
                this.registerDeferred(request);
            } else if (deploymentTask) {
                request = deploymentTask.fetch();
                request.done(_.bind(function() {
                    if (deploymentTask.get('status') == 'running') {
                        this.updateProgress();
                        this.scheduleUpdate();
                    } else {
                        this.model.fetch();
                        app.navbar.refresh();
                    }
                }, this));
                this.registerDeferred(request);
            }
        },
        updateProgress: function() {
            var task = this.model.task('deploy', 'running');
            if (task) {
                var progress = task.get('progress') || 0;
                this.$('.bar').css('width', (progress > 3 ? progress : 3) + '%');
            }
        },
        initialize: function() {
            this.model.on('change', this.render, this);
        },
        render: function() {
            this.$el.html(this.template({cluster: this.model}));
            this.updateProgress();
            if (this.model.task('cluster_deletion', ['running', 'ready'])) {
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

    return ClustersPage;
});
