define(
[
    'text!templates/common/breadcrumb.html'
],
function(breadcrumbTemplate) {
    var views = {}

    views.Breadcrumb = Backbone.View.extend({
        tagName: 'ul',
        className: 'breadcrumb',
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
