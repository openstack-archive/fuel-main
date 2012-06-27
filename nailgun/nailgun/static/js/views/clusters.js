define(
[
    'models',
    'views/dialogs',
    'text!templates/clusters/page.html',
    'text!templates/clusters/cluster.html'
],
function(models, dialogViews, clustersPageTemplate, clusterTemplate) {
    var views = {}

    views.ClustersPage = Backbone.View.extend({
        className: 'span12',
        template: _.template(clustersPageTemplate),
        events: {
            'click .js-create-cluster': 'createCluster'
        },
        createCluster: function(e) {
            e.preventDefault();
            (new dialogViews.createClusterDialog()).render();
        },
        initialize: function() {
            this.model.bind('reset', this.render, this);
            this.model.bind('add', this.render, this);
        },
        render: function() {
            this.$el.html(this.template({clusters: this.model}));
            this.$('.cluster_list').html(new views.ClusterList({model: this.model}).render().el);
            return this;
        }
    });

    views.ClusterList = Backbone.View.extend({
        className: 'row',
        initialize: function() {
            this.model.bind('reset', this.render, this);
            this.model.bind('add', this.render, this);
        },
        render: function() {
            if (this.model.length) {
                this.$el.html('');
                this.model.each(_.bind(function(cluster) {
                    this.$el.append(new views.Cluster({model: cluster}).render().el);
                }, this));
            } else {
                this.$el.html('<div class="span12"><div class="alert">There are no clusters</div></div>');
            }
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
