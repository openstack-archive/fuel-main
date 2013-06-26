define(
[
    'views/common',
    'views/dialogs',
    'text!templates/release/list.html',
    'text!templates/release/release.html'
],
function(commonViews, dialogViews, releasesListTemplate, releaseTemplate) {
    'use strict';

    var ReleasesPage, Release;

    ReleasesPage = commonViews.Page.extend({
        navbarActiveElement: 'releases',
        breadcrumbsPath: [['Home', '#'], 'Releases'],
        title: 'Releases',
        updateInterval: 3000,
        template: _.template(releasesListTemplate),
        scheduleUpdate: function() {
            if (app.navbar.getDownloadTasks().length) {
                this.registerDeferred($.timeout(this.updateInterval).done(_.bind(this.update, this)));
            }
        },
        update: function() {
            if (app.navbar.getDownloadTasks().length) {
                this.registerDeferred(app.navbar.fetchTasks().always(_.bind(this.scheduleUpdate, this)));
            }
        },
        initialize: function() {
            this.scheduleUpdate();
        },
        render: function() {
            this.tearDownRegisteredSubViews();
            this.$el.html(this.template({releases: this.collection}));
            this.collection.each(function(release) {
                var releaseView = new Release({release: release});
                this.registerSubView(releaseView);
                this.$('.releases-table tbody').append(releaseView.render().el);
            }, this);
            return this;
        }
    });

    Release = Backbone.View.extend({
        tagName: 'tr',
        template: _.template(releaseTemplate),
        'events': {
            'click .btn-rhel-setup': 'showRhelLicenseCredentials'
        },
        showRhelLicenseCredentials: function() {
            var dialog = new dialogViews.RhelCredentialsDialog({releaseId: this.release.id});
            this.registerSubView(dialog);
            dialog.render();
        },
        downloadFinished: function() {
            this.$('.release-status').removeClass('not-available').html('Available');
            this.$('.btn-rhel-setup, #download_progress').html('');
        },
        updateProgress: function(){
            var task = app.navbar.getDownloadTasks(this.release.id);
            if (task) {
                this.$('.btn-rhel-setup').hide();
                this.$('#download_progress').show();
                this.$('.bar').css('width', task.get('progress')+'%');
            }
        },
        initialize: function(options) {
            _.defaults(this, options);
            app.navbar.tasks.on('add', this.onNewTask, this);
            this.bindTaskEvents(app.navbar.getDownloadTasks(this.release.id));
        },
        bindTaskEvents: function(task) {
            if (task && task.get('name') == 'download_release' && task.getRelease() == this.release.id) {
                task.on('change:status', this.downloadFinished, this);
                task.on('change:progress', this.updateProgress, this);
            }
            return task;
        },
        onNewTask: function(task) {
            return this.bindTaskEvents(task) && this.updateProgress();
        },
        render: function() {
            this.tearDownRegisteredSubViews();
            this.$el.html(this.template({release: this.release}));
            this.updateProgress();
            return this;
        }
    });

    return ReleasesPage;
});
