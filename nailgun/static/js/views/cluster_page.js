define(
[
    'models',
    'views/common',
    'views/dialogs',
    'views/cluster_page_tabs/nodes_tab',
    'views/cluster_page_tabs/network_tab',
    'views/cluster_page_tabs/settings_tab',
    'views/cluster_page_tabs/logs_tab',
    'views/cluster_page_tabs/actions_tab',
    'text!templates/cluster/page.html',
    'text!templates/cluster/deployment_result.html',
    'text!templates/cluster/deployment_control.html'
],
function(models, commonViews, dialogViews, NodesTab, NetworkTab, SettingsTab, LogsTab, ActionsTab, clusterPageTemplate, deploymentResultTemplate, deploymentControlTemplate) {
    'use strict';
    var ClusterPage, DeploymentResult, DeploymentControl;

    ClusterPage = commonViews.Page.extend({
        navbarActiveElement: 'clusters',
        breadcrumbsPath: function() {
            return [['Home', '#'], ['OpenStack Installations', '#clusters'], this.model.get('name')];
        },
        title: function() {
            return this.model.get('name');
        },
        tabs: ['nodes', 'network', 'settings', 'logs', 'actions'],
        updateInterval: 5000,
        template: _.template(clusterPageTemplate),
        events: {
            'click .task-result .close': 'dismissTaskResult',
            'click .rollback': 'discardChanges',
            'click .deploy-btn:not(.disabled)': 'displayChanges'
        },
        removeVerificationTask: function() {
            var deferred;
            var task = this.model.task('verify_networks');
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
            this.model.task('deploy').destroy();
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
        scheduleUpdate: function() {
            if (this.model.task('deploy', 'running')) {
                this.timeout = _.delay(_.bind(this.update, this), this.updateInterval);
            }
        },
        update: function() {
            var complete = _.after(2, _.bind(this.scheduleUpdate, this));
            var task = this.model.task('deploy', 'running');
            if (task) {
                task.fetch({complete: complete}).done(_.bind(function() {
                    if (task.get('status') != 'running') {
                        this.deploymentFinished();
                    }
                }, this));
                this.model.get('nodes').fetch({data: {cluster_id: this.model.id}, complete: complete});
            }
        },
        deploymentStarted: function() {
            this.model.fetch().done(_.bind(function() {
                this.unbindEventsWhileDeploying();
                this.scheduleUpdate();
            }, this));
        },
        deploymentFinished: function() {
            this.model.fetch();
            app.navbar.stats.nodes.fetch();
            app.navbar.notifications.fetch();
        },
        beforeTearDown: function() {
            if (this.timeout) {
                clearTimeout(this.timeout);
            }
        },
        initialize: function(options) {
            _.defaults(this, options);
            this.model.bind('change:tasks', this.bindTasksEvents, this);
            this.bindTasksEvents();
            this.model.bind('change:nodes', this.bindNodesEvents, this);
            this.model.bind('change:changes', this.renderDeploymentControl, this);
            this.bindNodesEvents();
            this.scheduleUpdate();
        },
        bindTasksEvents: function() {
            this.model.get('tasks').bind('reset', this.renderDeploymentResult, this);
            this.model.get('tasks').bind('reset', this.renderDeploymentControl, this);
            if (arguments.length) {
                this.renderDeploymentResult();
                this.renderDeploymentControl();
            }
        },
        bindNodesEvents: function() {
            this.model.get('nodes').bind('reset', this.renderDeploymentControl, this);
            if (arguments.length) {
                this.renderDeploymentControl();
            }
        },
        unbindEventsWhileDeploying: function() {
            // unbind some events while deploying to make progress bar movement smooth and prevent showing wrong cluster status for a moment.
            // these events will be rebound automatically by fetching the whole cluster on deployment finish
            var task = this.model.task('deploy', 'running');
            if (task) {
                task.unbind('change:status', this.deploymentResult.render, this.deploymentResult);
                task.unbind('change:status', this.deploymentControl.render, this.deploymentControl);
                this.model.get('nodes').unbind('reset', this.renderDeploymentControl, this);
            }
        },
        renderDeploymentResult: function() {
            if (this.deploymentResult) {
                this.deploymentResult.tearDown();
            }
            this.deploymentResult = new DeploymentResult({model: this.model});
            this.registerSubView(this.deploymentResult);
            this.$('.deployment-result').html(this.deploymentResult.render().el);
        },
        renderDeploymentControl: function() {
            if (this.deploymentControl) {
                this.deploymentControl.tearDown();
            }
            this.deploymentControl = new DeploymentControl({model: this.model});
            this.registerSubView(this.deploymentControl);
            this.$('.deployment-control').html(this.deploymentControl.render().el);
        },
        render: function() {
            this.$el.html(this.template({
                cluster: this.model,
                tabs: this.tabs,
                activeTab: this.activeTab,
                renaming: this.renaming
            }));
            this.renderDeploymentResult();
            this.renderDeploymentControl();
            this.unbindEventsWhileDeploying();

            var tabs = {
                'nodes': NodesTab,
                'network': NetworkTab,
                'settings': SettingsTab,
                'actions': ActionsTab,
                'logs': LogsTab
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
        initialize: function(options) {
            var task = this.model.task('deploy');
            if (task) {
                task.bind('change:status', this.render, this);
            }
        },
        render: function() {
            this.$el.html(this.template({cluster: this.model}));
            return this;
        }
    });

    DeploymentControl = Backbone.View.extend({
        template: _.template(deploymentControlTemplate),
        initialize: function(options) {
            this.model.bind('change:status', this.render, this);
            var task = this.model.task('deploy');
            if (task) {
                task.bind('change:status', this.render, this);
                task.bind('change:progress', this.updateProgress, this);
            }
        },
        updateProgress: function() {
            var task = this.model.task('deploy', 'running');
            if (task) {
                var progress = task.get('progress') || 0;
                this.$('.bar').css('width', (progress > 3 ? progress : 3) + '%');
                this.$('.percentage').text((progress > 3 ? progress : 3) + '%');
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
