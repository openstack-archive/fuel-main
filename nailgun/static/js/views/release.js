define(
[
    'text!templates/release/list.html'
],
function(releaseListTemplate) {
    var views = {}

    views.ReleasesPage = Backbone.View.extend({
        className: 'span12',
        template: _.template(releaseListTemplate),
        initialize: function() {
            this.collection.bind('reset', this.render, this);
        },
        render: function() {
            this.$el.html(this.template({releases: this.collection}));
            return this;
        }
    });

    return views;
});
