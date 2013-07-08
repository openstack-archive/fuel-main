define(
[
    'models',
    'views/common',
    'views/dialogs',
    'text!templates/cluster/healthcheck_tab.html',
    'text!templates/cluster/healthcheck_testset.html'
],
function(models, commonViews, dialogViews, healthcheckTabTemplate, healthcheckTestSetTemplate) {
    'use strict';

    var HealthCheckTab, TestSet;

    HealthCheckTab = commonViews.Tab.extend({
        template: _.template(healthcheckTabTemplate),
        events: {
            'change input[type=checkbox]': 'calculateRunTestsButtonState',
            'click .run-tests-btn:not(:disabled)': 'runTests'
        },
        isLocked: function() {
            return this.model.get('status') == 'new' || !!this.model.task('deploy', 'running');
        },
        disableControls: function(disable) {
            this.$('.btn, input').attr('disabled', disable || this.isLocked());
        },
        calculateRunTestsButtonState: function() {
            this.$('.run-tests-btn').attr('disabled', !this.$('input[type=checkbox]:checked').length);
        },
        runTests: function() {
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
                ).done(_.bind(this.render, this));
            } else {
                _.extend(this, this.model.get('ostf'));
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
                        testrun: this.testruns.findWhere({testset: testset.id}),
                        tests: new models.Tests(this.tests.where({test_set: testset.id})),
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
        initialize: function(options) {
            _.defaults(this, options);
        },
        render: function() {
            this.tearDownRegisteredSubViews();
            this.$el.html(this.template({
                testset: this.testset,
                testrun: this.testrun,
                tests: this.tests
            }));
            return this;
        }
    });

    return HealthCheckTab;
});
