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
    'models',    
    'text!templates/support/page.html'
],
function(commonViews, models, supportPageTemplate) {
    'use strict';

    var SupportPage = commonViews.Page.extend({
        navbarActiveElement: 'support',
        breadcrumbsPath: [['Home', '#'], 'Support'],
        title: 'Support',
        updateInterval: 2000,
        template: _.template(supportPageTemplate),
        events: {
            'click .download-logs:not(.disabled)': 'downloadLogs'
        },
        scheduleUpdate: function() {
            var task = this.logsPackageTasks.filterTasks({name: 'dump'});
            if (this.timeout) {
                this.timeout.clear();
            }
            if (_.isUndefined(task[0]) || task[0].get('progress') < 100 ) {
                this.registerDeferred(this.timeout = $.timeout(this.updateInterval).done(_.bind(this.update, this)));
            } else {
                if (task[0].get('status') == 'error') {
                    this.$('.download-logs-error').text(task[0].get('message'));
                    this.$('.download-logs-error').removeClass('hide');
                } else {

                    this.$('.donwload-logs-link').removeClass('hide');
                    this.$('.donwload-logs-link > a').attr('href', task[0].get('message'));
                }
                this.$('.genereate-logs').addClass('hide');
                this.$('.download-logs').removeClass('disabled');
            }
        },
        update: function() {
            this.registerDeferred(this.logsPackageTasks.fetch().always(_.bind(this.scheduleUpdate, this)));
        },
        downloadLogs: function() {
            var task = new models.LogsPackage();
            task.save({}, {method: 'PUT'});
            this.$('.download-logs').addClass('disabled');
            this.$('.donwload-logs-link').addClass('hide');
            this.$('.download-logs-error').addlass('hide');
            this.$('.genereate-logs').removeClass('hide');
            this.logsPackageTasks = new models.Tasks();
            this.logsPackageTasks.fetch();
            this.scheduleUpdate();
        },
        initialize: function(options) {
            _.defaults(this, options);
            this.model = new models.FuelKey();
            this.model.fetch();
            this.model.on('change', this.render, this);
        },
        render: function() {
            this.$el.html(this.template());
            return this;
        }
    });

    return SupportPage;
});
