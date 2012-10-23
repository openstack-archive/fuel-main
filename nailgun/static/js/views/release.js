define(
[
    'text!templates/release/list.html'
],
function(releaseListTemplate) {
    'use strict';

    var views = {};

    views.ReleasesPage = Backbone.View.extend({
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
