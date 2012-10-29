define(
[
    'models',
    'text!templates/common/navbar.html',
    'text!templates/common/nodes_stats.html',
    'text!templates/common/nodes_stats_popover.html',
    'text!templates/common/breadcrumb.html'
],
function(models, navbarTemplate, nodesStatsTemplate, nodesStatsPopoverTemplate, breadcrumbTemplate) {
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
            this.$('.nodes-summary-container').html(this.stats.render().el);
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
                    this.$('.stats-' + role).css('width', (100 * stats[role] / stats.total) + '%');
                    stats[role] = this.nodes.where({role: role}).length;
                }, this);
                if (this.popoverVisible) {
                    this.hidePopover();
                    this.showPopover();
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
