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
        template: _.template(clustersPageTemplate),
        render: function() {
            this.$el.html(this.template({clusters: this.collection}));
            this.$('.cluster-list').html(new views.ClusterList({collection: this.collection}).render().el);
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
            this.collection.bind('add', this.render, this);
        },
        render: function() {
            this.$el.html('');
            this.collection.each(_.bind(function(cluster) {
                this.$el.append(new views.Cluster({model: cluster}).render().el);
            }, this));
            this.$el.append(this.newClusterTemplate());
            return this;
        }
    });

    views.Cluster = Backbone.View.extend({
        tagName: 'a',
        className: 'span3 clusterbox',
        template: _.template(clusterTemplate),
        initialize: function() {
            this.model.bind('change', this.render, this);
        },
        render: function() {
            this.$el.attr('href', '#cluster/' + this.model.id + '/nodes');
            this.$el.html(this.template({cluster: this.model}));
            return this;
        }
    });

    return views;
});
