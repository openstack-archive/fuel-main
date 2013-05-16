define(
[
    'utils',
    'models',
    'views/common',
    'views/dialogs',
    'text!templates/notifications/list.html'
],
function(utils, models, commonViews, dialogViews, notificationsListTemplate) {
    'use strict';

    var NotificationsPage = commonViews.Page.extend({
        navbarActiveElement: null,
        breadcrumbsPath: [['Home', '#'], 'Notifications'],
        title: 'Notifications',
        template: _.template(notificationsListTemplate),
        templateHelpers: _.pick(utils, 'urlify'),
        events: {
            'click .new' : 'markAsRead',
            'click .discover' : 'showNodeInfo'
        },
        markAsRead: function(e) {
            var notification = this.notifications.get($(e.currentTarget).data('id'));
            notification.toJSON = function() {
                return _.pick(notification.attributes, 'id', 'status');
            };
            notification.save({status: 'read'})
                .done(_.bind(function() {
                    this.notifications.trigger('sync');
                }, this));
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
            this.notifications.on('sync', this.render, this);
        },
        render: function() {
            this.$el.html(this.template(_.extend({notifications: this.notifications}, this.templateHelpers)));
            return this;
        }
    });

    return NotificationsPage;
});
