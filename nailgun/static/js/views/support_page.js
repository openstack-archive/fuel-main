define(
[
    'views/common',
    'text!templates/support/page.html'
],
function(commonViews, supportPageTemplate) {
    'use strict';

    var SupportPage = commonViews.Page.extend({
        navbarActiveElement: 'support',
        breadcrumbsPath: [['Home', '#'], 'Support'],
        title: 'Support',
        template: _.template(supportPageTemplate),
        events: {
            'click .download-logs:not(.disabled)': 'downloadLogs'
        },
        downloadLogs: function() {
            this.$('.download-logs').addClass('disabled');
            window.location = '/api/logs/package';
        },
        render: function() {
            this.$el.html(this.template());
            return this;
        }
    });

    return SupportPage;
});
