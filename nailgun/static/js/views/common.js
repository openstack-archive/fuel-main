define(
[
    'models',
    'text!templates/common/navbar.html',
    'text!templates/common/nodes_stats.html',
    'text!templates/common/nodes_stats_popover.html',
    'text!templates/common/notifications.html',
    'text!templates/common/notifications_popover.html',
    'text!templates/common/breadcrumb.html'
],
function(models, navbarTemplate, nodesStatsTemplate, nodesStatsPopoverTemplate, notificationsTemplate, notificationsPopoverTemplate, breadcrumbTemplate) {
    'use strict';

    var views = {};

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
        popoverTemplate: _.template(nodesStatsPopoverTemplate),
        popoverVisible: false,
        stats: {},
        events: {
            'mouseenter': 'showPopover',
            'mouseleave': 'hidePopover'
        },
        showPopover: function() {
            if (!this.popoverVisible) {
                this.popoverVisible = true;
                this.$el.popover({
                    placement: 'bottom',
                    trigger: 'manual',
                    title: 'Usage Statistics',
                    content: this.popoverTemplate({stats: this.stats})
                }).popover('show');
            }
        },
        hidePopover: function() {
            if (this.popoverVisible) {
                this.popoverVisible = false;
                this.$el.popover('destroy');
            }
        },
        scheduleUpdate: function() {
            _.delay(_.bind(this.update, this), this.updateInterval);
        },
        update: function() {
            this.nodes.fetch({complete: _.bind(this.scheduleUpdate, this)});
        },
        updateStats: function() {
            var stats = {};
            var roles = ['controller', 'compute', 'storage'];
            if (this.nodes.deferred.state() != 'pending') {
                _.each(roles, function(role) {
                    stats[role] = this.nodes.where({role: role}).length;
                }, this);
                stats.total = this.nodes.length;
                stats.unallocated = stats.total - stats.controller - stats.compute - stats.storage;
            }
            if (!_.isEqual(stats, this.stats)) {
                this.stats = stats;
                _.each(roles, function(role) {
                    stats[role] = this.nodes.where({role: role}).length;
                }, this);
                if (this.popoverVisible) {
                    this.hidePopover();
                    this.showPopover();
                }
                if (stats.unallocated) {
                    _.each(roles, function(role) {
                        this.$('.stats-' + role).width(stats.total ? (100 * stats[role] / stats.total) + '%' : 0);
                    }, this);
                } else if (stats.total) {
                    // all nodes have role assigned, working around "odd pixel" bug
                    var containerWidth = this.$('.nodes-summary-stat').width();
                    var barsWidth = 0;
                    _.each(_.initial(roles), function(role) {
                        var barWidth = Math.round(containerWidth * stats[role] / stats.total);
                        barsWidth += barWidth;
                        this.$('.stats-' + role).width(barWidth);
                    }, this);
                    this.$('.stats-' + _.last(roles)).width(Math.floor(containerWidth - barsWidth));
                } else {
                    this.$('.bar').width(0);
                }
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
        updateInterval: 5000,
        template: _.template(notificationsTemplate),
        popoverTemplate: _.template(notificationsPopoverTemplate),
        popoverVisible: false,
        displayCount: 5,
        events: {
            'click': 'togglePopover'
        },
        getUnreadNotifications: function() {
            return _.filter(this.notifications.last(this.displayCount), function(notification) {return notification.get('status') == 'unread';});
        },
        hidePopover: function(e) {
            if (this.popoverVisible && !$(e.target).closest($('.message-list-placeholder')).length) {
                this.popoverVisible = false;
                $('.message-list-placeholder').remove();
            }
        },
        togglePopover: function(e) {
            if (!this.popoverVisible) {
                if ($(e.target).closest(this.$el).length) {
                    this.popoverVisible = true;
                    $('.navigation-bar').after(this.popoverTemplate({notifications: this.notifications.last(this.displayCount)}));
                    _.each(this.getUnreadNotifications(), function(notification) {
                        notification.set({'status': 'read'});
                    });
                    Backbone.sync('update', this.notifications).done(_.bind(this.render, this));
                }
            } else {
                this.hidePopover(e);
            }
        },
        beforeTearDown: function() {
            $('html').off(this.eventNamespace);
        },
        scheduleUpdate: function() {
            if (this.getUnreadNotifications().length) {
                this.render();
            }
            _.delay(_.bind(this.update, this), this.updateInterval);
        },
        update: function() {
            this.notifications.fetch({complete: _.bind(this.scheduleUpdate, this)});
        },
        initialize: function(options) {
            this.eventNamespace = 'click.click-notofications';
            this.notifications = new models.Notifications();
            this.notifications.deferred = this.notifications.fetch();
            this.notifications.deferred.done(_.bind( function() {
                this.scheduleUpdate();
                $('html').on(this.eventNamespace, _.bind(function(e){
                    if (!$(e.target).closest(this.$el).length) {
                        this.hidePopover(e);
                    }
                }, this));
            }, this));
        },
        render: function() {
            this.$el.html(this.template({notifications: this.notifications}));
            return this;
        }
    });

    views.Breadcrumb = Backbone.View.extend({
        className: 'container',
        template: _.template(breadcrumbTemplate),
        path: [],
        setPath: function() {
            this.path = arguments;
            this.render();
        },
        render: function() {
            this.$el.html(this.template({path: this.path}));
            return this;
        }
    });

    return views;
});
