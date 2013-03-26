define(
[
    'models',
    'views/common',
    'views/dialogs',
    'text!templates/notifications/list.html'
],
function(models, commonViews, dialogViews, notificationsListTemplate) {
    'use strict';

    var NotificationsPage = commonViews.Page.extend({
        navbarActiveElement: null,
        breadcrumbsPath: [['Home', '#'], 'Notifications'],
        title: 'Notifications',
        template: _.template(notificationsListTemplate),
        events: {
            'click .discover' : 'showNodeInfo'
        },
        showNodeInfo: function(e) {
            if ($(e.target).data('node')) {
                var node = this.nodes.get($(e.target).data('node'));
                var dialog = new dialogViews.ShowNodeInfoDialog({node: node});
                this.registerSubView(dialog);
                dialog.render();
            }
        },
        initialize: function(options) {
            _.defaults(this, options);
            this.notifications.bind('sync', this.render, this);
        },
        render: function() {
            this.$el.html(this.template({notifications: this.notifications}));
            return this;
        }
    });

    return NotificationsPage;
});
