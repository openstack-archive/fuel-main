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
    'views/dialogs',
    'text!templates/common/navbar.html',
    'text!templates/common/nodes_stats.html',
    'text!templates/common/notifications.html',
    'text!templates/common/notifications_popover.html',
    'text!templates/common/breadcrumb.html',
    'text!templates/common/footer.html',
    'text!templates/common/rhel_credentials.html'
],
function(utils, models, dialogViews, navbarTemplate, nodesStatsTemplate, notificationsTemplate, notificationsPopoverTemplate, breadcrumbsTemplate, footerTemplate, rhelCredentialsTemplate) {
    'use strict';

    var views = {};

    views.Page = Backbone.View.extend({
        navbarActiveElement: null,
        breadcrumbsPath: null,
        title: null,
        updateNavbar: function() {
            app.navbar.setActive(_.result(this, 'navbarActiveElement'));
        },
        updateBreadcrumbs: function() {
            var breadcrumbsPath = _.isFunction(this.breadcrumbsPath) ? this.breadcrumbsPath() : this.breadcrumbsPath;
            app.breadcrumbs.setPath(_.result(this, 'breadcrumbsPath'));
        },
        updateTitle: function() {
            var defaultTitle = 'Fuel Dashboard';
            var title = _.result(this, 'title');
            document.title = title ? defaultTitle + ' - ' + title : defaultTitle;
        }
    });

    views.Tab = Backbone.View.extend({
        initialize: function(options) {
            _.defaults(this, options);
        }
    });

    views.Navbar = Backbone.View.extend({
        className: 'container',
        template: _.template(navbarTemplate),
        updateInterval: 20000,
        notificationsDisplayCount: 5,
        setActive: function(element) {
            this.$('a.active').removeClass('active');
            this.$('a[href="#' + element + '"]').addClass('active');
        },
        scheduleUpdate: function() {
            this.registerDeferred($.timeout(this.updateInterval).done(_.bind(this.update, this)));
        },
        update: function() {
            this.refresh().always(_.bind(this.scheduleUpdate, this));
        },
        refresh: function() {
            return $.when(this.statistics.fetch(), this.notifications.fetch({limit: this.notificationsDisplayCount}));
        },
        initialize: function(options) {
            this.elements = _.isArray(options.elements) ? options.elements : [];
            this.statistics = new models.NodesStatistics();
            this.notifications = new models.Notifications();
            $.when(this.statistics.deferred = this.statistics.fetch(), this.notifications.deferred = this.notifications.fetch({limit: this.notificationsDisplayCount})).done(_.bind(this.scheduleUpdate, this));
        },
        render: function() {
            this.tearDownRegisteredSubViews();
            if (!this.$('.navigation-bar-ul a').length) {
                this.$el.html(this.template({elements: this.elements}));
            }
            this.stats = new views.NodesStats({statistics: this.statistics, navbar: this});
            this.registerSubView(this.stats);
            this.$('.nodes-summary-container').html(this.stats.render().el);
            this.notificationsButton = new views.Notifications({collection: this.notifications, navbar: this});
            this.registerSubView(this.notificationsButton);
            this.$('.notifications').html(this.notificationsButton.render().el);
            this.popover = new views.NotificationsPopover({collection: this.notifications, navbar: this});
            this.registerSubView(this.popover);
            this.$('.notification-wrapper').html(this.popover.render().el);
            return this;
        }
    });

    views.NodesStats = Backbone.View.extend({
        template: _.template(nodesStatsTemplate),
        initialize: function(options) {
            _.defaults(this, options);
            this.statistics.on('change', this.render, this);
        },
        render: function() {
            if (this.statistics.deferred.state() == 'resolved') {
                this.$el.html(this.template({stats: this.statistics}));
            }
            return this;
        }
    });

    views.Notifications = Backbone.View.extend({
        template: _.template(notificationsTemplate),
        events: {
            'click .icon-comment': 'togglePopover',
            'click .badge': 'togglePopover'
        },
        togglePopover: function(e) {
            this.navbar.popover.toggle();
        },
        initialize: function(options) {
            _.defaults(this, options);
            this.collection.on('sync', this.render, this);
        },
        render: function() {
            this.$el.html(this.template({notifications: this.collection}));
            return this;
        }
    });

    views.NotificationsPopover = Backbone.View.extend({
        template: _.template(notificationsPopoverTemplate),
        templateHelpers: _.pick(utils, 'urlify'),
        visible: false,
        events: {
            'click .discover' : 'showNodeInfo'
        },
        showNodeInfo: function(e) {
            var nodeId = $(e.currentTarget).data('node');
            if (nodeId) {
                this.toggle();
                var node = new models.Node({id: nodeId});
                node.deferred = node.fetch();
                var dialog = new dialogViews.ShowNodeInfoDialog({node: node});
                this.registerSubView(dialog);
                dialog.render();
            }
        },
        toggle: function() {
            this.visible = !this.visible;
            this.render();
        },
        hide: function(e) {
            if (this.visible && (!e || (!$(e.target).closest(this.navbar.notificationsButton.el).length && !$(e.target).closest(this.el).length))) {
                this.visible = false;
                this.render();
            }
        },
        markAsRead: function() {
            var notificationsToMark = new models.Notifications(this.collection.where({status : 'unread'}));
            if (notificationsToMark.length) {
                notificationsToMark.toJSON = function() {
                    return notificationsToMark.map(function(notification) {
                        notification.set({status: 'read'}, {silent: true});
                        return _.pick(notification.attributes, 'id', 'status');
                    }, this);
                };
                Backbone.sync('update', notificationsToMark).done(_.bind(function() {
                    this.collection.trigger('sync');
                }, this));
            }
        },
        beforeTearDown: function() {
            this.unbindEvents();
        },
        initialize: function(options) {
            _.defaults(this, options);
            this.collection.bind('add', this.render, this);
            this.eventNamespace = 'click.click-notifications';
        },
        bindEvents: function() {
            $('html').on(this.eventNamespace, _.bind(this.hide, this));
            Backbone.history.on('route', this.hide, this);
        },
        unbindEvents: function() {
            $('html').off(this.eventNamespace);
            Backbone.history.off('route', this.hide, this);
        },
        render: function() {
            if (this.visible) {
                this.$el.html(this.template(_.extend({
                    notifications: this.collection,
                    displayCount: this.navbar.notificationsDisplayCount,
                    showMore: (Backbone.history.getHash() != 'notifications') && this.collection.length
                }, this.templateHelpers)));
                this.markAsRead();
                this.bindEvents();
            } else {
                this.$el.html('');
                this.unbindEvents();
            }
            return this;
        }
    });

    views.Breadcrumbs = Backbone.View.extend({
        className: 'container',
        template: _.template(breadcrumbsTemplate),
        path: [],
        setPath: function(path) {
            this.path = path;
            this.render();
        },
        render: function() {
            this.$el.html(this.template({path: this.path}));
            return this;
        }
    });

    views.Footer = Backbone.View.extend({
        template: _.template(footerTemplate),
        initialize: function(options) {
            $.ajax({url: '/api/version'}).done(_.bind(function(data) {
                this.version = data.release;
                this.render();
            }, this));
        },
        render: function() {
            this.$el.html(this.template({version: this.version}));
            return this;
        }
    });

    views.RhelCredentialsForm = Backbone.View.extend({
        visible: true,
        template: _.template(rhelCredentialsTemplate),
        events: {
            'change input[name=license-type]': 'toggle',
            'keydown input': 'onInputKeydown'
        },
        toggle: function() {
            this.$('.control-group.error').removeClass('error').find('.help-inline').html('');
            this.$('.control-group.rhn').toggle();
        },
        onInputKeydown: function(e) {
            this.$(e.currentTarget).parents('.control-group').removeClass('error').find('.help-inline').html('');
        },
        showValidationError: function(errors) {
            _.each(errors, function(message, field) {
                this.$('*[name=' + field + ']').closest('.control-group').addClass('error').find('.help-inline').text(message);
            }, this);
        },
        setCredentials: function() {
            var licenseType = this.$('input[name=license-type]:checked').val();
            var accountData = {
                license_type: licenseType,
                username: this.$('input[name=username]').val(),
                password: this.$('input[name=password]').val(),
                satellite: licenseType == 'rhn' ? this.$('input[name=satellite]').val() : '',
                activation_key: licenseType == 'rhn' ? this.$('input[name=activation_key]').val() : ''
            };
            return this.redHatAccount.set(accountData, {validate: true});
        },
        saveCredentials: function() {
            var task = new models.Task();
            var options = {
                method: 'POST',
                url: '/api/redhat/setup',
                data: JSON.stringify(_.extend({release_id: this.dialog.release.id}, this.redHatAccount.attributes))
            };
            task.deferred = task.save({}, options);
            return task;
        },
        initialize: function(options) {
            _.defaults(this, options);
            if (!this.redHatAccount) {
                this.redHatAccount = new models.RedHatAccount();
                this.redHatAccount.deferred = this.redHatAccount.fetch();
            }
            this.redHatAccount.on('sync', this.render, this);
            this.redHatAccount.on('invalid', function(model, errors) {
                this.showValidationError(errors);
            }, this);
        },
        render: function() {
            this.$el.html(_.result(this, 'visible') ? this.template({account: this.redHatAccount}) : '');
            this.$('.control-group.rhn').toggle(this.redHatAccount.get('license_type') == 'rhn');
            return this;
        }
    });

    return views;
});
