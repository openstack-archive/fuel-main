define(
[
    'models',
    'views/dialogs',
    'text!templates/clusters/page.html',
    'text!templates/clusters/cluster.html',
    'text!templates/clusters/new.html'
],
function(models, dialogViews, clustersPageTemplate, clusterTemplate, newClusterTemplate) {
    var views = {}

    views.ClustersPage = Backbone.View.extend({
        className: 'span12',
        template: _.template(clustersPageTemplate),
        render: function() {
            this.$el.html(this.template({clusters: this.model}));
            this.$('.cluster-list').html(new views.ClusterList({model: this.model}).render().el);
            return this;
        }
    });

    views.ClusterList = Backbone.View.extend({
        className: 'row',
        newClusterTemplate: _.template(newClusterTemplate),
        events: {
            'click .create': 'createCluster'
        },
        createCluster: function(e) {
            e.preventDefault();
            (new dialogViews.createClusterDialog({model: this.model})).render();
        },
        initialize: function() {
            this.model.bind('reset', this.render, this);
            this.model.bind('add', this.render, this);
        },
        render: function() {
            this.$el.html('');
            this.model.each(_.bind(function(cluster) {
                this.$el.append(new views.Cluster({model: cluster}).render().el);
            }, this));
            this.$el.append(this.newClusterTemplate());
            return this;
        }
    });

    views.Cluster = Backbone.View.extend({
        className: 'span3',
        template: _.template(clusterTemplate),
        initialize: function() {
            this.model.bind('change', this.render, this);
        },
        render: function() {
            this.$el.html(this.template({cluster: this.model}));
            return this;
        }
    });

    return views;
});
