define(
[
    'models',
    'views/common',
    'views/dialogs',
    'text!templates/notifications/list.html'
],
function(models, commonViews, dialogViews, notificationsListTemplate) {
    'use strict';

    var views = {};

    views.NotificationsPage = commonViews.Page.extend({
        navbarActiveElement: null,
        breadcrumbsPath: [['Home', '#'], 'Notifications'],
        title: 'Notifications',
        template: _.template(notificationsListTemplate),
        events: {
            'click .discover' : 'showNodeInfo'
        },
        showNodeInfo: function(e) {
            var node = new models.Node(this.nodes.filter(function(node) {return node.id == $(e.target).data('node');}));
            var dialog = new dialogViews.ShowNodeInfoDialog({node: node});
            this.registerSubView(dialog);
            dialog.render();
        },
        initialize: function() {
            this.collection.bind('reset', this.render, this);
            this.nodes = new models.Nodes();
            this.nodes.deferred = this.nodes.fetch();
            this.nodes.deferred.done(_.bind(this.render, this));
        },
        render: function() {
            this.$el.html(this.template({notifications: this.collection}));
            return this;
        }
    });

    return views;
});
