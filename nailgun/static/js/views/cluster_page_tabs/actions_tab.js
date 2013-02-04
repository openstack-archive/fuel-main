define(
[
    'models',
    'views/common',
    'views/dialogs',
    'text!templates/cluster/actions_tab.html'
],
function(models, commonViews, dialogViews, actionsTabTemplate) {
    'use strict';

    var ActionsTab = commonViews.Tab.extend({
        template: _.template(actionsTabTemplate),
        events: {
            'click .rename-cluster-form .apply-name-btn': 'applyNewClusterName',
            'keydown .rename-cluster-form input': 'onClusterNameInputKeydown',
            'click .delete-cluster-form .delete-cluster-btn': 'deleteCluster'
        },
        applyNewClusterName: function() {
            var name = $.trim(this.$('.rename-cluster-form input').val());
            if (name != '' && name != this.model.get('name')) {
                this.$('.rename-cluster-form input, .rename-cluster-form .apply-name-btn').attr('disabled', true);
                this.model.update({name: name}, {
                    complete: function() {
                        this.page.updateBreadcrumbs();
                        this.page.updateTitle();
                        this.render();
                    },
                    context: this
                });
            }
        },
        onClusterNameInputKeydown: function(e) {
            if (e.which == 13) {
                this.applyNewClusterName();
            }
        },
        deleteCluster: function() {
            var deleteClusterDialogView = new dialogViews.RemoveClusterDialog({model: this.model});
            this.registerSubView(deleteClusterDialogView);
            deleteClusterDialogView.render();
        },
        initialize: function(options) {
            _.defaults(this, options);
            this.model.bind('change:name', this.render, this);
        },
        render: function() {
            this.$el.html(this.template({cluster: this.model}));
            return this;
        }
    });

    return ActionsTab;
});
