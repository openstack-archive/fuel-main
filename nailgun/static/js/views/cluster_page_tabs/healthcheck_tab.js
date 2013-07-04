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
        },
        initialize: function(options) {
            _.defaults(this, options);
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
        },
        render: function() {
            this.tearDownRegisteredSubViews();
            this.$el.html(this.template({cluster: this.model}));
            this.$('.testsets').html('');
            this.testsets.each(function(testset) {
                var testsetView = new TestSet({
                    testset: testset,
                    tests: new models.Tests(this.tests.where({testset: testset.id})),
                    tab: this
                });
                this.registerSubView(testsetView);
                this.$('.testsets').append(testsetView.render().el);
            }, this);
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
                tests: this.tests
            }));
            return this;
        }
    });

    return HealthCheckTab;
});
