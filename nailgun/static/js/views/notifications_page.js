/*
 * Copyright 2013 Mirantis, Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use this file except in compliance with the License. You may obtain
 * a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations
 * under the License.
**/
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
            var nodeId = $(e.currentTarget).data('node');
            if (nodeId) {
                var node = new models.Node({id: nodeId});
                node.deferred = node.fetch();
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
