define(
[
    'models',
    'text!templates/common/navbar.html',
    'text!templates/common/nodes_stats.html',
    'text!templates/common/notifications.html',
    'text!templates/common/notifications_popover.html',
    'text!templates/common/breadcrumb.html'
],
function(models, navbarTemplate, nodesStatsTemplate, notificationsTemplate, notificationsPopoverTemplate, breadcrumbsTemplate) {
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
        setActive: function(element) {
            this.$('.nav > li.active').removeClass('active');
            this.$('a[href="#' + element + '"]').parent().addClass('active');
        },
        initialize: function(options) {
            this.elements = _.isArray(options.elements) ? options.elements : [];
        },
        render: function() {
            this.$el.html(this.template({elements: this.elements}));
            this.stats = new views.NodesStats();
            this.registerSubView(this.stats);
            this.$('.nodes-summary-container').html(this.stats.render().el);
            this.notifications = new views.Notifications();
            this.registerSubView(this.notifications);
            this.$('.notifications').html(this.notifications.render().el);
            return this;
        }
    });

    views.NodesStats = Backbone.View.extend({
        updateInterval: 30000,
        template: _.template(nodesStatsTemplate),
        stats: {},
        scheduleUpdate: function() {
            _.delay(_.bind(this.update, this), this.updateInterval);
        },
        update: function() {
            this.nodes.fetch({complete: _.bind(this.scheduleUpdate, this)});
        },
        updateStats: function() {
            var roles = ['controller', 'compute', 'storage'];
            if (this.nodes.deferred.state() != 'pending') {
                _.each(roles, function(role) {
                    this.stats[role] = this.nodes.where({role: role}).length;
                }, this);
                this.stats.total = this.nodes.length;
                this.stats.unallocated = this.stats.total - this.stats.controller - this.stats.compute - this.stats.storage;
                this.render();
            }
        },
        initialize: function(options) {
            this.nodes = new models.Nodes();
            this.nodes.deferred = this.nodes.fetch();
            this.nodes.deferred.done(_.bind(this.scheduleUpdate, this));
            this.nodes.bind('reset', this.updateStats, this);
        },
        render: function() {
            this.$el.html(this.template({stats: this.stats}));
            return this;
        }
    });

    views.Notifications = Backbone.View.extend({
        updateInterval: 20000,
        template: _.template(notificationsTemplate),
        popoverTemplate: _.template(notificationsPopoverTemplate),
        popoverVisible: false,
        displayCount: 5,
        events: {
            'click': 'togglePopover'
        },
        getUnreadNotifications: function() {
            return this.collection.where({status : 'unread'});
        },
        hidePopover: function(e) {
            if (this.popoverVisible && !$(e.target).closest($('.message-list-placeholder')).length) {
                $('html').off(this.eventNamespace);
                this.popoverVisible = false;
                $('.message-list-placeholder').remove();
            }
        },
        togglePopover: function(e) {
            if (!this.popoverVisible && $(e.target).closest(this.$el).length) {
                $('html').off(this.eventNamespace);
                $('html').on(this.eventNamespace, _.after(2, _.bind(function(e) {
                    this.hidePopover(e);
                }, this)));
                this.popoverVisible = true;
                $('.navigation-bar').after(this.popoverTemplate({notifications: this.collection.last(this.displayCount)}));
                _.each(this.getUnreadNotifications(), function(notification) {
                    notification.set({'status': 'read'});
                });
                Backbone.sync('update', this.collection).done(_.bind(this.render, this));
            }
        },
        scheduleUpdate: function() {
            if (this.getUnreadNotifications().length) {
                this.render();
            }
            _.delay(_.bind(this.update, this), this.updateInterval);
        },
        update: function() {
            this.collection.fetch({complete: _.bind(this.scheduleUpdate, this)});
        },
        beforeTearDown: function() {
            $('html').off(this.eventNamespace);
        },
        initialize: function(options) {
            this.eventNamespace = 'click.click-notifications';
            this.collection = new models.Notifications();
            this.collection.bind('reset', this.render, this);
            this.collection.deferred = this.collection.fetch();
            this.collection.deferred.done(_.bind(this.scheduleUpdate, this));
        },
        render: function() {
            this.$el.html(this.template({notifications: this.collection}));
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
