define(
[
    'models',
    'views/common',
    'views/dialogs',
    'text!templates/cluster/healthcheck_tab.html',
    'text!templates/cluster/healthcheck_testset.html',
    'text!templates/cluster/healthcheck_tests.html'
],
function(models, commonViews, dialogViews, healthcheckTabTemplate, healthcheckTestSetTemplate, healthcheckTestsTemplate) {
    'use strict';

    var HealthCheckTab, TestSet;

    HealthCheckTab = commonViews.Tab.extend({
        template: _.template(healthcheckTabTemplate),
        updateInterval: 5000,
        events: {
            'change input[type=checkbox]': 'calculateRunTestsButtonState',
            'click .run-tests-btn:not(:disabled)': 'runTests'
        },
        isLocked: function() {
            return this.model.get('status') == 'new' || this.hasRunningTests() || !!this.model.task('deploy', 'running');
        },
        disableControls: function(disable) {
            this.$('.btn, input').prop('disabled', disable || this.isLocked());
        },
        calculateRunTestsButtonState: function() {
            this.$('.run-tests-btn').prop('disabled', !this.$('input[type=checkbox]:checked').length || this.hasRunningTests());
        },
        hasRunningTests: function() {
            return !!_.intersection(_.pluck(_.flatten(this.testruns.pluck('tests'), true), 'status'), ['running', 'wait_running']).length;
        },
        scheduleUpdate: function() {
            if (this.hasRunningTests()) {
                this.registerDeferred($.timeout(this.updateInterval).done(_.bind(this.update, this)));
            }
        },
        update: function() {
            this.registerDeferred(
                this.testruns.fetch({url: _.result(this.testruns, 'url') + '/last/' + this.model.id})
                    .done(_.bind(function() {
                        if (!this.hasRunningTests()) {
                            this.disableControls(false);
                            this.calculateRunTestsButtonState();
                            this.$('input[type=checkbox]').prop('checked', false);
                        }
                    }, this))
                    .always(_.bind(this.scheduleUpdate, this))
            );
        },
        runTests: function() {
            var testruns = new models.TestRuns();
            _.each(this.subViews, function(subView) {
                if (subView instanceof TestSet && subView.$('input[type=checkbox]:checked').length) {
                    var testrun = new models.TestRun({
                        testset: subView.testset.id,
                        metadata: {
                            config: {},
                            cluster_id: this.model.id
                        }
                    });
                    testruns.add(testrun);
                }
            }, this);
            this.disableControls(true);
            Backbone.sync('create', testruns).done(_.bind(this.update, this));
        },
        updateTestRuns: function() {
            _.each(this.subViews, function(subView) {
                if (subView instanceof TestSet) {
                    var testrun = this.testruns.findWhere({testset: subView.testset.id});
                    if (testrun) {
                        subView.testrun.set(testrun.attributes);
                    }
                }
            }, this);
        },
        bindTaskEvents: function(task) {
            return task.get('name') == 'deploy' ? task.on('change:status', this.render, this) : null;
        },
        onNewTask: function(task) {
            return this.bindTaskEvents(task) && this.render();
        },
        initialize: function(options) {
            _.defaults(this, options);
            this.model.on('change:status', this.render, this);
            this.model.get('tasks').each(this.bindTaskEvents, this);
            this.model.get('tasks').on('add', this.onNewTask, this);
            if (!this.model.get('ostf')) {
                var ostf = {};
                ostf.testsets = new models.TestSets();
                ostf.tests = new models.Tests();
                ostf.testruns = new models.TestRuns();
                this.model.set({'ostf': ostf}, {silent: true});
                _.extend(this, ostf);
                $.when(
                    this.testsets.deferred = this.testsets.fetch(),
                    this.tests.fetch(),
                    this.testruns.fetch({url: _.result(this.testruns, 'url') + '/last/' + this.model.id})
                ).done(_.bind(function() {
                    this.render();
                    this.testruns.on('sync', this.updateTestRuns, this);
                    this.scheduleUpdate();
                }, this));
            } else {
                _.extend(this, this.model.get('ostf'));
                this.scheduleUpdate();
            }
        },
        render: function() {
            this.tearDownRegisteredSubViews();
            this.$el.html(this.template({cluster: this.model}));
            if (this.testsets.deferred.state() != 'pending') {
                this.$('.testsets').html('');
                this.testsets.each(function(testset) {
                    var testsetView = new TestSet({
                        testset: testset,
                        testrun: this.testruns.findWhere({testset: testset.id}) || new models.TestRun(),
                        tests: new models.Tests(this.tests.where({testset: testset.id})),
                        tab: this
                    });
                    this.registerSubView(testsetView);
                    this.$('.testsets').append(testsetView.render().el);
                }, this);
            }
            this.disableControls(false);
            this.calculateRunTestsButtonState();
            return this;
        }
    });

    TestSet = Backbone.View.extend({
        template: _.template(healthcheckTestSetTemplate),
        testsTemplate: _.template(healthcheckTestsTemplate),
        initialize: function(options) {
            _.defaults(this, options);
            this.testrun.on('change', this.renderTests, this);
        },
        renderTests: function() {
            this.$('tbody').html(this.testsTemplate({testrun: this.testrun, tests: this.tests}));
        },
        render: function() {
            this.$el.html(this.template({testset: this.testset}));
            this.renderTests();
            return this;
        }
    });

    return HealthCheckTab;
});
