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
    'utils',
    'models',
    'views/common',
    'views/dialogs',
    'views/cluster_page_tabs/nodes_tab',
    'views/cluster_page_tabs/network_tab',
    'views/cluster_page_tabs/settings_tab',
    'views/cluster_page_tabs/logs_tab',
    'views/cluster_page_tabs/actions_tab',
    'views/cluster_page_tabs/healthcheck_tab',
    'text!templates/cluster/page.html',
    'text!templates/cluster/deployment_result.html',
    'text!templates/cluster/deployment_control.html'
],
function(utils, models, commonViews, dialogViews, NodesTab, NetworkTab, SettingsTab, LogsTab, ActionsTab, HealthCheckTab, clusterPageTemplate, deploymentResultTemplate, deploymentControlTemplate) {
    'use strict';
    var ClusterPage, DeploymentResult, DeploymentControl;

    ClusterPage = commonViews.Page.extend({
        navbarActiveElement: 'clusters',
        breadcrumbsPath: function() {
            return [['Home', '#'], ['Environments', '#clusters'], this.model.get('name')];
        },
        title: function() {
            return this.model.get('name');
        },
        tabs: ['nodes', 'network', 'settings', 'logs', 'actions', 'healthcheck'],
        updateInterval: 5000,
        template: _.template(clusterPageTemplate),
        events: {
            'click .task-result .close': 'dismissTaskResult',
            'click .rollback': 'discardChanges',
            'click .deploy-btn:not(.disabled)': 'onDeployRequest'
        },
        removeVerificationTask: function() {
            var deferred;
            var task = this.model.task('verify_networks') || this.model.task('check_networks') || this.model.task('check_before_deployment');
            if (task && task.get('status') != 'running') {
                this.model.get('tasks').remove(task);
                deferred = task.destroy({silent: true});
            } else {
                deferred = new $.Deferred();
                deferred.resolve();
            }
            return deferred;
        },
        dismissTaskResult: function() {
            this.$('.task-result').remove();
            this.model.deployTask().destroy();
        },
        discardChanges: function() {
            var dialog = new dialogViews.DiscardChangesDialog({model: this.model});
            this.registerSubView(dialog);
            dialog.render();
        },
        displayChanges: function() {
            var dialog = new dialogViews.DisplayChangesDialog({model: this.model});
            this.registerSubView(dialog);
            dialog.render();
        },
        discardSettingsChanges: function(options) {
            var dialog = new dialogViews.DiscardSettingsChangesDialog(options);
            this.registerSubView(dialog);
            dialog.render();
        },
        onNameChange: function() {
            this.updateBreadcrumbs();
            this.updateTitle();
        },
        onDeployRequest: function() {
            if (_.result(this.tab, 'hasChanges')) {
                this.discardSettingsChanges({cb: _.bind(function() {
                    this.tab.revertChanges();
                    this.displayChanges();
                }, this)});
            } else {
                this.displayChanges();
            }
        },
        onTabLeave: function(e) {
            var href = $(e.currentTarget).attr('href');
            if (Backbone.history.getHash() != href.substr(1) && _.result(this.tab, 'hasChanges')) {
                e.preventDefault();
                this.discardSettingsChanges({
                    verification: !!(this.model.task('verify_networks', 'running') || this.model.task('check_networks', 'running')),
                    cb: _.bind(function() {
                        app.navigate(href, {trigger: true});
                    }, this)
                });
            }
        },
        scheduleUpdate: function() {
            var task = this.model.deployTask('running') || this.model.task('verify_networks', 'running') || this.tasks.getDownloadTask(this.model.get('release').id);
            if (!this.pollingAborted && task) {
                this.registerDeferred($.timeout(this.updateInterval).done(_.bind(this.update, this)));
            }
        },
        update: function() {
            if (this.pollingAborted) {
                return;
            }
            var complete = _.after(2, _.bind(this.scheduleUpdate, this));
            var deploymentTask = this.model.deployTask('running');
            if (deploymentTask) {
                this.registerDeferred(deploymentTask.fetch().done(_.bind(function() {
                    if (deploymentTask.get('status') != 'running') {
                        this.deploymentFinished();
                    }
                }, this)).always(complete));
                this.registerDeferred(this.model.get('nodes').fetch({data: {cluster_id: this.model.id}}).always(complete));
            }
            var verificationTask = this.model.task('verify_networks', 'running');
            if (verificationTask) {
                this.registerDeferred(verificationTask.fetch().always(_.bind(this.scheduleUpdate, this)));
            }
            var downloadTask = this.tasks.getDownloadTask(this.model.get('release').id);
            if (downloadTask) {
                this.registerDeferred(this.tasks.fetch().always(_.bind(this.scheduleUpdate, this)));
            }
        },
        deploymentStarted: function() {
            $.when(this.model.fetch(), this.model.fetchRelated('nodes'), this.model.fetchRelated('tasks')).done(_.bind(function() {
                this.unbindEventsWhileDeploying();
                this.scheduleUpdate();
            }, this));
        },
        deploymentFinished: function() {
            $.when(this.model.fetch(), this.model.fetchRelated('nodes'), this.model.fetchRelated('tasks')).done(_.bind(function() {
                this.rebindEventsAfterDeployment();
                app.navbar.refresh();
            }, this));
        },
        unbindEventsWhileDeploying: function() {
            // unbind some events while deploying to make progress bar movement smooth and prevent showing wrong cluster status for a moment.
            var task = this.model.task('deploy','running');
            if (task) {
                task.off('change:status', this.deploymentResult.render, this.deploymentResult);
                task.off('change:status', this.deploymentControl.render, this.deploymentControl);
            }
            task = this.model.task('check_before_deployment');
            if (task) {
                if (task.get('status') == 'error') {
                    this.renderdeploymentResult();
                } else {
                    task.destroy();
                }
            }
        },
        rebindEventsAfterDeployment: function() {
            // rebind temporarily unbound events
            _([this.deploymentResult, this.deploymentControl]).invoke('onNewTask', this.model.deployTask());
        },
        beforeTearDown: function() {
            this.pollingAborted = true;
            $(window).off('beforeunload.' + this.eventNamespace);
            $('body').off('click.' + this.eventNamespace);
        },
        onBeforeunloadEvent: function() {
            if (_.result(this.tab, 'hasChanges')) {
                return dialogViews.DiscardSettingsChangesDialog.prototype.defaultMessage;
            }
        },
        initialize: function(options) {
            _.defaults(this, options);
            this.model.on('change:name', this.onNameChange, this);
            this.scheduleUpdate();
            this.eventNamespace = 'unsavedchanges' + this.activeTab;
            $(window).on('beforeunload.' + this.eventNamespace, _.bind(this.onBeforeunloadEvent, this));
            $('body').on('click.' + this.eventNamespace, 'a[href^=#]', _.bind(this.onTabLeave, this));
        },
        renderdeploymentResult: function() {
            this.deploymentResult = new DeploymentResult({model: this.model, page: this});
            this.registerSubView(this.deploymentResult);
            this.$('.deployment-result').html(this.deploymentResult.render().el);
        },
        render: function() {
            this.tearDownRegisteredSubViews();
            this.$el.html(this.template({
                cluster: this.model,
                tabs: this.tabs,
                activeTab: this.activeTab,
                renaming: this.renaming
            }));

            this.renderdeploymentResult();
            this.deploymentControl = new DeploymentControl({model: this.model, page: this});
            this.registerSubView(this.deploymentControl);
            this.$('.deployment-control').html(this.deploymentControl.render().el);

            var tabs = {
                'nodes': NodesTab,
                'network': NetworkTab,
                'settings': SettingsTab,
                'actions': ActionsTab,
                'logs': LogsTab,
                'healthcheck': HealthCheckTab
            };
            if (_.has(tabs, this.activeTab)) {
                this.tab = new tabs[this.activeTab]({model: this.model, tabOptions: this.tabOptions, page: this});
                this.$('#tab-' + this.activeTab).html(this.tab.render().el);
                this.registerSubView(this.tab);
            }

            return this;
        }
    });

    DeploymentResult = Backbone.View.extend({
        template: _.template(deploymentResultTemplate),
        templateHelpers: _.pick(utils, 'urlify'),
        initialize: function(options) {
            this.model.get('tasks').each(this.bindTaskEvents, this);
            this.model.get('tasks').on('add', this.onNewTask, this);
        },
        bindTaskEvents: function(task) {
            return task.get('name') == 'deploy' ? task.on('change:status', this.render, this) : null;
        },
        onNewTask: function(task) {
            return this.bindTaskEvents(task) && this.render();
        },
        render: function() {
            this.$el.html(this.template(_.extend({cluster: this.model}, this.templateHelpers)));
            return this;
        }
    });

    DeploymentControl = Backbone.View.extend({
        template: _.template(deploymentControlTemplate),
        initialize: function(options) {
            this.model.on('change:changes', this.render, this);
            this.model.get('tasks').each(this.bindTaskEvents, this);
            this.model.get('tasks').on('add', this.onNewTask, this);
            this.model.get('nodes').each(this.bindNodeEvents, this);
            this.model.get('nodes').on('resize', this.render, this);
            this.model.get('nodes').on('add', this.onNewNode, this);
            this.bindTaskEvents(app.page.tasks.getDownloadTask(this.model.get('release').id));
        },
        bindTaskEvents: function(task) {
            if (task && (task.get('name') == 'deploy' || task.get('name') == 'download_release')) {
                task.on('change:status', this.render, this);
                task.on('change:progress', this.updateProgress, this);
                return task;
            }
            return null;
        },
        bindNodeEvents: function(node) {
            return node.on('change:pending_addition change:pending_deletion', this.render, this);
        },
        onNewTask: function(task) {
            return this.bindTaskEvents(task) && this.render();
        },
        onNewNode: function(node) {
            return this.bindNodeEvents(node) && this.render();
        },
        updateProgress: function() {
            var task = this.model.deployTask('running') || app.page.tasks.getDownloadTask(this.model.get('release').id);
            if (task) {
                var progress = task.get('progress') || 0;
                this.$('.bar').css('width', (progress > 3 ? progress : 3) + '%');
                this.$('.percentage').text(progress + '%');
            }
        },
        render: function() {
            this.$el.html(this.template({cluster: this.model}));
            this.updateProgress();
            return this;
        }
    });

    return ClusterPage;
});
