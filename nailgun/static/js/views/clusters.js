define(
[
    'models',
    'views/dialogs',
    'text!templates/clusters/page.html',
    'text!templates/clusters/cluster.html',
    'text!templates/clusters/new.html'
],
function(models, dialogViews, clustersPageTemplate, clusterTemplate, newClusterTemplate) {
    'use strict';

    var views = {};

    views.ClustersPage = Backbone.View.extend({
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
            if (this.model.task('cluster_deletion', 'running')) {
                _.delay(_.bind(this.update, this), this.updateInterval);
            } else {
                this.render();
            }
        },
        update: function() {
            var task = this.model.task('cluster_deletion');
            var cluster = this;
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
            }
            return this;
        }
    });

    return views;
});
