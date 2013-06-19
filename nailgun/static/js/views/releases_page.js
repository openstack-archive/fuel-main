define(
[
    'models',
    'views/common',
    'views/dialogs',
    'text!templates/release/list.html'
],
function(models, commonViews, dialogViews, releaseListTemplate) {
    'use strict';

    var ReleasesPage = commonViews.Page.extend({
        navbarActiveElement: 'releases',
        breadcrumbsPath: [['Home', '#'], 'OpenStack Releases'],
        title: 'OpenStack Releases',
        template: _.template(releaseListTemplate),
        'events': {
            'click .rhel-license': 'showAccountSettings'
        },
        showAccountSettings: function() {
            var dialog = new dialogViews.RhelLicenseDialog({model: this.model});
            this.registerSubView(dialog);
            dialog.render();
        },
        downloadStarted: function() {
            this.$('.rhel-license, #download_progress').toggleClass('hide');
            this.progress = 0;
            this.renderProgress();
        },
        renderProgress: function(){
            if (this.progress <= 100){
                this.progress += 1;
                this.$('.bar').css('width', this.progress+'%');
                window.setTimeout(_.bind(this.renderProgress, this), 1500);
            } else {
                this.$('#download_progress, .available, .not-available').toggleClass('hide');

            }
        },
        initialize: function() {
            this.collection.on('sync', this.render, this);
        },
        render: function() {
            this.$el.html(this.template({releases: this.collection}));
            return this;
        }
    });

    return ReleasesPage;
});
