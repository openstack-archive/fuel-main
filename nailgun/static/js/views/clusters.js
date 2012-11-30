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
        createCluster: function(e) {
            e.preventDefault();
            (new dialogViews.CreateClusterDialog({collection: this.collection})).render();
        },
        initialize: function() {
            this.collection.bind('reset', this.render, this);
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
        updateInterval: 500,
        scheduleUpdate: function() {
            if (this.model.task('cluster_deletion', 'running')) {
                _.delay(_.bind(this.update, this), this.updateInterval);
            } else {
                this.model.collection.trigger('reset');
            }
        },
        update: function() {
            var complete = _.after(2, _.bind(this.scheduleUpdate, this));
            this.model.get('tasks').fetch({data: {cluster_id: this.model.id}, complete: complete});
        },
        initialize: function() {
            this.model.bind('change', this.render, this);
            if (this.model.task('cluster_deletion', 'running')) {
                this.$el.removeAttr('href').addClass('disabledCluster');
                this.update();
            }
        },
        render: function() {
            this.$el.attr('href', '#cluster/' + this.model.id + '/nodes');
            this.$el.html(this.template({cluster: this.model}));
            return this;
        }
    });

    return views;
});
