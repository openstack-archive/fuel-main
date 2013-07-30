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
            if (this.tasks.filterTasks({name: 'setup_redhat'}).length) {
                this.registerDeferred($.timeout(this.updateInterval).done(_.bind(this.update, this)));
            }
        },
        update: function() {
            if (this.tasks.filterTasks({name: 'setup_redhat'}).length) {
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
        setupFinished: function() {
            var setupTask = this.tasks.filterTasks({name: 'setup_redhat', status: 'ready', release: this.release.id})[0];
            if (setupTask) {
                setupTask.destroy();
            }
            this.release.fetch();
            app.navbar.refresh();
        },
        updateProgress: function(){
            var task = this.tasks.filterTasks({name: 'setup_redhat', status: 'running', release: this.release.id})[0];
            if (task) {
                this.$('.bar').css('width', task.get('progress') + '%');
                this.$('.bar-title span').text(task.get('progress') + '%');
            }
        },
        initialize: function(options) {
            _.defaults(this, options);
            this.tasks.each(this.bindTaskEvents, this);
            this.tasks.on('add', this.onNewTask, this);
            this.release.on('change', this.render, this);
        },
        bindTaskEvents: function(task) {
            if (task.get('name') == 'setup_redhat' && task.get('result').release_info.release_id == this.release.id) {
                task.on('change:status', this.setupFinished, this);
                task.on('change:progress', this.updateProgress, this);
                return task;
            }
            return null;
        },
        onNewTask: function(task) {
            if (this.bindTaskEvents(task)) {
                this.release.fetch();
                this.updateProgress();
            }
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
