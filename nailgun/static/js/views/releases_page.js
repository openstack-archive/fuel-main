/*
 * Copyright 2013 Mirantis, Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use this file except in compliance with the License. You may obtain
 * a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations
 * under the License.
**/
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
            if (this.tasks.filterTasks({name: 'download_release', status: 'running'}).length) {
                this.registerDeferred($.timeout(this.updateInterval).done(_.bind(this.update, this)));
            }
        },
        update: function() {
            if (this.tasks.filterTasks({name: 'download_release', status: 'running'}).length) {
                this.registerDeferred(this.tasks.fetch().always(_.bind(this.scheduleUpdate, this)));
            }
        },
        initialize: function(options) {
            _.defaults(this, options);
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
            var dialog = new dialogViews.RhelCredentialsDialog({release: this.release});
            this.registerSubView(dialog);
            dialog.render();
        },
        downloadFinished: function() {
            this.$('.download_progress').html('');
            var task = app.page.tasks.filterTasks({name: 'download_release', release: this.release.id})[0];
            if (task.get('status') == 'error'){
                this.$('.release-status span').html('Error');
                this.$('.btn-rhel-setup').show();
            } else {
                this.$('.release-status').removeClass('not-available').html('Available');
            }
        },
        updateProgress: function(){
            var task = app.page.tasks.getDownloadTask(this.release.id);
            if (task) {
                this.$('.btn-rhel-setup').hide();
                this.$('.download_progress').show();
                this.$('.bar').css('width', task.get('progress')+'%');
            }
        },
        initialize: function(options) {
            _.defaults(this, options);
            app.page.tasks.on('add', this.onNewTask, this);
            this.bindTaskEvents(app.page.tasks.getDownloadTask(this.release.id));
        },
        bindTaskEvents: function(task) {
            if (task && task.get('name') == 'download_release' && task.get('result').release_info.release_id == this.release.id) {
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
