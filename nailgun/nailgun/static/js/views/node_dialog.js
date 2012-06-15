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

            this.$('.cluster-nodes').html(new views.nodeDialogNodeList({model: this.model.get('nodes'), checked: true}).render().el);
            this.availableNodes = new models.Nodes;
            this.availableNodes.fetch({
                data: {cluster_id: ''},
                success: _.bind(function() {
                    this.$('.available-nodes').html(new views.nodeDialogNodeList({model: this.availableNodes, checked: false}).render().el);
                }, this)
            });
            return this;
        }
    });

    views.nodeDialogNodeList = Backbone.View.extend({
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
