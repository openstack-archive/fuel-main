define(
[
    'models',
    'text!templates/common/navbar.html',
    'text!templates/common/breadcrumb.html'
],
function(models, navbarTemplate, breadcrumbTemplate) {
    var views = {};

    views.Navbar = Backbone.View.extend({
        updateInterval: 30000,
        className: 'container',
        template: _.template(navbarTemplate),
        scheduleUpdate: function() {
            _.delay(_.bind(this.update, this), this.updateInterval);
        },
        update: function() {
            this.nodes.fetch({complete: _.bind(this.scheduleUpdate, this)});
        },
        setActive: function(element) {
            this.$('.nav > li.active').removeClass('active');
            this.$('a[href="#' + element + '"]').parent().addClass('active');
        },
        initialize: function(options) {
            this.elements = _.isArray(options.elements) ? options.elements : [];
            this.nodes = new models.Nodes();
            this.nodes.deferred = this.nodes.fetch();
            this.nodes.deferred.done(_.bind(this.scheduleUpdate, this));
            this.nodes.bind('reset', this.render, this);
        },
        render: function() {
            this.$el.html(this.template({elements: this.elements, nodes: this.nodes}));
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
