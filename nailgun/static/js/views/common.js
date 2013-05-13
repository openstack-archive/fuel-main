define(
[
    'models',
    'views/dialogs',
    'text!templates/common/navbar.html',
    'text!templates/common/nodes_stats.html',
    'text!templates/common/notifications.html',
    'text!templates/common/notifications_popover.html',
    'text!templates/common/breadcrumb.html',
    'text!templates/common/footer.html'
],
function(models, dialogViews, navbarTemplate, nodesStatsTemplate, notificationsTemplate, notificationsPopoverTemplate, breadcrumbsTemplate, footerTemplate) {
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
            var defaultTitle = 'FuelWeb Dashboard';
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
            return $.when(this.nodes.fetch(), this.notifications.fetch());
        },
        initialize: function(options) {
            this.elements = _.isArray(options.elements) ? options.elements : [];
            this.nodes = new models.Nodes();
            this.notifications = new models.Notifications();
            $.when(this.nodes.deferred = this.nodes.fetch(), this.notifications.deferred = this.notifications.fetch()).done(_.bind(this.scheduleUpdate, this));
        },
        render: function() {
            this.tearDownRegisteredSubViews();
            if (!this.$('.navigation-bar-ul a').length) {
                this.$el.html(this.template({elements: this.elements}));
            }
            this.stats = new views.NodesStats({collection: this.nodes, navbar: this});
            this.registerSubView(this.stats);
            this.$('.nodes-summary-container').html(this.stats.render().el);
            this.notificationsButton = new views.Notifications({collection: this.notifications, navbar: this});
            this.registerSubView(this.notificationsButton);
            this.$('.notifications').html(this.notificationsButton.render().el);
            this.popover = new views.NotificationsPopover({nodes: this.nodes, collection: this.notifications, navbar: this});
            this.registerSubView(this.popover);
            this.$('.notification-wrapper').html(this.popover.render().el);
            return this;
        }
    });

    views.NodesStats = Backbone.View.extend({
        template: _.template(nodesStatsTemplate),
        stats: {},
        initialize: function(options) {
            _.defaults(this, options);
            this.collection.on('sync', this.render, this);
        },
        calculateStats: function() {
            this.stats.total = this.collection.length;
            this.stats.unallocated = this.collection.filter(function(node) {return !node.get('role');}).length;
        },
        render: function() {
            if (this.collection.deferred.state() == 'resolved') {
                this.calculateStats();
                this.$el.html(this.template({stats: this.stats}));
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
        visible: false,
        events: {
            'click .discover' : 'showNodeInfo'
        },
        showNodeInfo: function(e) {
            if ($(e.target).data('node')) {
                this.toggle();
                var node = this.nodes.get($(e.target).data('node'));
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
                this.$el.html(this.template({
                    notifications: this.collection,
                    displayCount: 5,
                    showMore: (Backbone.history.getHash() != 'notifications') && this.collection.length
                }));
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

    return views;
});
