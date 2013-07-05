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
            return false;//this.model.get('status') == 'new' || !!this.model.task('deploy', 'running');
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
            this.testsets = new models.TestSets([
                {id: 'testset-nova', name: 'Nova Tests'},
                {id: 'testset-glance', name: 'Glance Tests'}
            ]);
            this.tests = new models.Tests([
                {id: 'test-nova-1', testset: 'testset-nova', name: 'Nova Test #1'},
                {id: 'test-nova-2', testset: 'testset-nova', name: 'Nova Test #2'},
                {id: 'test-nova-3', testset: 'testset-nova', name: 'Nova Test #3'},
                {id: 'test-glance-1', testset: 'testset-glance', name: 'Glance Test #1'},
                {id: 'test-glance-2', testset: 'testset-glance', name: 'Glance Test #2'},
            ]);
            this.testruns = new models.TestRuns([
                {id: 1, testset: 'testset-nova', tests: [
                    {id: 'test-nova-1', status: 'success'},
                    {id: 'test-nova-3', status: 'error', message: 'Error occured!'}
                ]},
                {id: 2, testset: 'testset-glance', tests: [
                    {id: 'test-glance-1', status: 'running'},
                    {id: 'test-glance-2', status: 'failure', message: 'Test failed!'}
                ]},
            ]);
        },
        render: function() {
            this.tearDownRegisteredSubViews();
            this.$el.html(this.template({cluster: this.model}));
            this.$('.testsets').html('');
            this.testsets.each(function(testset) {
                var testsetView = new TestSet({
                    testset: testset,
                    testrun: this.testruns.findWhere({testset: testset.id}),
                    tests: new models.Tests(this.tests.where({testset: testset.id})),
                    tab: this
                });
                this.registerSubView(testsetView);
                this.$('.testsets').append(testsetView.render().el);
            }, this);
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
