define(
[
    'models',
    'text!templates/node_dialog/dialog.html',
    'text!templates/node_dialog/dialog_node_list.html'
],
function(models, nodeDialogTemplate, nodeDialogNodeListTemplate) {
    var views = {}

    views.nodeDialog = Backbone.View.extend({
        className: 'modal fade',
        template: _.template(nodeDialogTemplate),
        events: {
            'click .js-save-changes': 'saveChanges'
        },
        saveChanges: function(e) {
            e && e.preventDefault();
            this.$el.modal('hide');
        },
        render: function() {
            this.$el.html(this.template());
            this.$el.on('hidden', function() {$(this).remove()});
            this.$el.modal();

            this.$('.cluster-nodes').html(new views.nodeDialogNodeList({model: this.model.get('nodes')}).render().el);
            this.availableNodes = new models.Nodes;
            this.availableNodes.fetch({
                data: {cluster_id: ''},
                success: _.bind(function() {
                    this.$('.available-nodes').html(new views.nodeDialogNodeList({model: this.availableNodes}).render().el);
                }, this)
            });
            return this;
        }
    });

    views.nodeDialogNodeList = Backbone.View.extend({
        template: _.template(nodeDialogNodeListTemplate),
        render: function() {
            this.$el.html(this.template({nodes: this.model}));
            return this;
        }
    });

    return views;
});
