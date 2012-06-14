define(
[
    'text!templates/release/list.html'
],
function(releaseListTemplate) {
    var views = {}

    views.ReleaseList = Backbone.View.extend({
        className: 'span12',
        template: _.template(releaseListTemplate),
        initialize: function() {
            this.model.bind('reset', this.render, this);
            //this.model.bind('add', this.render, this);
        },
        render: function() {
            this.$el.html(this.template({releases: this.model}));
            return this;
        }
    });

    return views;
});
