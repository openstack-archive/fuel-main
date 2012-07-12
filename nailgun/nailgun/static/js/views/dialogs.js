define(
[
    'models',
    'text!templates/dialogs/add_remove_nodes.html',
    'text!templates/dialogs/create_cluster.html',
    'text!templates/dialogs/node_list.html'
],
function(models, addRemoveNodesDialogTemplate, createClusterDialogTemplate, nodeDialogNodeListTemplate) {
    var views = {}

    views.addRemoveNodesDialog = Backbone.View.extend({
        className: 'modal fade',
        template: _.template(addRemoveNodesDialogTemplate),
        events: {
            'click .js-save-changes': 'saveChanges',
            'click .dialog-node': 'toggleNode'
        },
        saveChanges: function(e) {
            e.preventDefault();
            var nodes = this.$('.node_check').map(function(){return $(this).attr('data-node-id')}).get();
            this.model.update({nodes: nodes});
            this.$el.modal('hide');
        },
        toggleNode: function(e) {
            $(e.currentTarget).toggleClass('node_check').toggleClass('node_uncheck');
        },
        render: function() {
            this.$el.html(this.template());
            this.$el.on('hidden', function() {$(this).remove()});
            this.$el.modal();

            this.$('.cluster-nodes').html(new views.nodeList({model: this.model.get('nodes'), checked: true}).render().el);
            this.availableNodes = new models.Nodes;
            this.availableNodes.fetch({
                data: {cluster_id: ''},
                success: _.bind(function() {
                    this.$('.available-nodes').html(new views.nodeList({model: this.availableNodes, checked: false}).render().el);
                }, this)
            });
            return this;
        }
    });

    views.createClusterDialog = Backbone.View.extend({
        className: 'modal fade',
        template: _.template(createClusterDialogTemplate),
        events: {
            'click .js-create-cluster': 'createCluster',
            'click .dialog-node': 'toggleNode'
        },
        createCluster: function(e) {
            e.preventDefault();
            this.$('.help-inline').text('');
            this.$('.control-group').removeClass('error');
            var nodes = this.$('.node_check').map(function(){return $(this).attr('data-node-id')}).get();
            var cluster = new models.Cluster();
            cluster.on('error', function(model, error) {
                _.each(error, function(message, field) {
                    this.$('*[name=' + field + '] ~ .help-inline').text(message);
                    this.$('*[name=' + field + ']').closest('.control-group').addClass('error');
                }, this);
            }, this);
            cluster.set({
                name: this.$('input[name=name]').attr('value'),
                release: this.$('select[name=release]').attr('value'),
                nodes: nodes
            });
            if (cluster.isValid()) {
                cluster.save({}, {success: _.bind(function() {
                    this.model.fetch();
                }, this)});
                this.$el.modal('hide');
            }
        },
        toggleNode: function(e) {
            $(e.currentTarget).toggleClass('node_check').toggleClass('node_uncheck');
        },
        render: function() {
            this.$el.html(this.template());
            this.$el.on('hidden', function() {$(this).remove()});
            this.$el.modal();

            this.releases = new models.Releases;
            this.releases.fetch({
                success: _.bind(function() {
                    this.releases.each(function(release) {
                        this.$('select[name=release]').append($('<option/>').attr('value', release.id).text(release.get('name')));
                    }, this);
                }, this)
            });

            this.availableNodes = new models.Nodes;
            this.availableNodes.fetch({
                data: {cluster_id: ''},
                success: _.bind(function() {
                    this.$('.available-nodes').html(new views.nodeList({model: this.availableNodes, checked: false}).render().el);
                }, this)
            });
            return this;
        }
    });

    views.nodeList = Backbone.View.extend({
        template: _.template(nodeDialogNodeListTemplate),
        initialize: function(options) {
            this.checked = options.checked;
        },
        render: function() {
            this.$el.html(this.template({nodes: this.model, checked: this.checked}));
            return this;
        }
    });

    return views;
});
