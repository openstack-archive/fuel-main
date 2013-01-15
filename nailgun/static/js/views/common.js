define(
[
    'models',
    'views/dialogs',
    'text!templates/common/navbar.html',
    'text!templates/common/nodes_stats.html',
    'text!templates/common/notifications.html',
    'text!templates/common/notifications_popover.html',
    'text!templates/common/breadcrumb.html'
],
function(models, dialogViews, navbarTemplate, nodesStatsTemplate, notificationsTemplate, notificationsPopoverTemplate, breadcrumbsTemplate) {
    'use strict';

    var views = {};

    views.Page = Backbone.View.extend({
        navbarActiveElement: null,
        breadcrumbsPath: null,
        title: null,
        updateNavbar: function() {
            var navbarActiveElement = _.isFunction(this.navbarActiveElement) ? this.navbarActiveElement() : this.navbarActiveElement;
            app.navbar.setActive(navbarActiveElement);
        },
        updateBreadcrumbs: function() {
            var breadcrumbsPath = _.isFunction(this.breadcrumbsPath) ? this.breadcrumbsPath() : this.breadcrumbsPath;
            app.breadcrumbs.setPath(breadcrumbsPath);
        },
        updateTitle: function() {
            var defaultTitle = 'Nailgun Dashboard';
            var title = _.isFunction(this.title) ? this.title() : this.title;
            document.title = title ? defaultTitle + ' - ' + title : defaultTitle;
        }
    });

    views.Navbar = Backbone.View.extend({
        className: 'container',
        template: _.template(navbarTemplate),
        updateInterval: 20000,
        popoverVisible: false,
        events: {
            'click .icon-comment': 'togglePopover',
            'click .badge': 'togglePopover'
        },
        hidePopover: function(e) {
            if (this.popoverVisible && (!$(e.target).closest($('.message-list-placeholder')).length || $(e.target).parent().hasClass('show-more-notifications'))) {
                $('html').off(this.eventNamespace);
                this.popoverVisible = false;
                $('.message-list-placeholder').parent().remove();
            }
        },
        togglePopover: function(e) {
            if (!this.popoverVisible && $(e.target).closest(this.$el).length) {
                $('html').off(this.eventNamespace);
                $('html').on(this.eventNamespace, _.after(2, _.bind(function(e) {
                    this.hidePopover(e);
                }, this)));
                this.popoverVisible = true;
                this.notificationsPopover = new views.NotificationsPopover({notifications: this.notifications, displayCount: 5});
                this.registerSubView(this.notificationsPopover);
                this.$el.after(this.notificationsPopover.render().el);
                _.each(this.notifications.where({status : 'unread'}), function(notification) {
                    notification.set({'status': 'read'});
                });
                Backbone.sync('update', this.notifications).done(_.bind(this.render, this));
            }
        },
        setActive: function(element) {
            this.$('.nav > li.active').removeClass('active');
            this.$('a[href="#' + element + '"]').parent().addClass('active');
        },
        scheduleUpdate: function() {
            _.delay(_.bind(this.update, this), this.updateInterval);
        },
        update: function() {
            var complete = _.after(2, _.bind(this.scheduleUpdate, this));
            this.nodes.fetch({complete: complete});
            this.notifications.fetch({complete: complete});
        },
        initialize: function(options) {
            this.eventNamespace = 'click.click-notifications';
            this.elements = _.isArray(options.elements) ? options.elements : [];
            var complete = _.after(2, _.bind(this.scheduleUpdate, this));
            this.nodes = new models.Nodes();
            this.nodes.fetch({complete: complete});
            this.nodes.bind('reset', this.render, this);
            this.notifications = new models.Notifications();
            this.notifications.fetch({complete: complete});
            this.notifications.bind('reset', this.render, this);
        },
        beforeTearDown: function() {
            $('html').off(this.eventNamespace);
        },
        render: function() {
            this.$el.html(this.template({elements: this.elements}));
            this.stats = new views.NodesStats({nodes: this.nodes});
            this.registerSubView(this.stats);
            this.$('.nodes-summary-container').html(this.stats.render().el);
            this.notificationsBar = new views.Notifications({notifications: this.notifications});
            this.registerSubView(this.notificationsBar);
            this.$('.notifications').html(this.notificationsBar.render().el);
            return this;
        }
    });

    views.NodesStats = Backbone.View.extend({
        template: _.template(nodesStatsTemplate),
        stats: {},
        initialize: function(options) {
            _.defaults(this, options);
        },
        render: function() {
            var roles = ['controller', 'compute', 'storage'];
            _.each(roles, function(role) {
                this.stats[role] = this.nodes.where({role: role}).length;
            }, this);
            this.stats.total = this.nodes.length;
            this.stats.unallocated = this.stats.total - this.stats.controller - this.stats.compute - this.stats.storage;
            this.$el.html(this.template({stats: this.stats}));
            return this;
        }
    });

    views.Notifications = Backbone.View.extend({
        template: _.template(notificationsTemplate),
        initialize: function(options) {
            _.defaults(this, options);
        },
        render: function() {
            this.$el.html(this.template({notifications: this.notifications}));
            return this;
        }
    });

    views.NotificationsPopover = Backbone.View.extend({
        template: _.template(notificationsPopoverTemplate),
        initialize: function(options) {
            _.defaults(this, options);
        },
        render: function() {
            this.$el.html(this.template({notifications: this.notifications, displayCount: 5}));
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

    return views;
});
