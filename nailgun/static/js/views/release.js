define(
[
    'views/common',
    'text!templates/release/list.html'
],
function(commonViews, releaseListTemplate) {
    'use strict';

    var views = {};

    views.ReleasesPage = commonViews.Page.extend({
        navbarActiveElement: 'releases',
        breadcrumbsPath: [['Home', '#'], 'Software Updates'],
        title: 'Software Updates',
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
