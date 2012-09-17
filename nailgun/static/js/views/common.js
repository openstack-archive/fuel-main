define(
[
    'text!templates/common/navbar.html',
    'text!templates/common/breadcrumb.html'
],
function(navbarTemplate, breadcrumbTemplate) {
    var views = {}

    views.Navbar = Backbone.View.extend({
        className: 'container',
        template: _.template(navbarTemplate),
        initialize: function(options) {
            this.elements = _.isArray(options.elements) ? options.elements : [];
        },
        setActive: function(element) {
            this.$('.nav > li.active').removeClass('active');
            this.$('a[href="#' + element + '"]').parent().addClass('active');
        },
        render: function() {
            this.$el.html(this.template({elements: this.elements}));
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
