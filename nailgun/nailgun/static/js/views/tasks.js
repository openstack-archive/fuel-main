define(
[
    'models',
    'text!templates/tasks/base_running.html',
    'text!templates/tasks/base_success.html',
    'text!templates/tasks/base_error.html',
],
function(models, runningTemplate, successTemplate, errorTemplate) {
    var views = {}

    views.Task = Backbone.View.extend({
        runningTemplate: _.template(runningTemplate),
        successTemplate: _.template(successTemplate),
        errorTemplate: _.template(errorTemplate),
        events: {
        },
        initialize: function() {
        },
        render: function() {
            console.log(this)
            var template = this.model.get('ready') ? this.model.get('error') ? this.errorTemplate : this.successTemplate : this.runningTemplate;
            this.$el.html(template({task: this.model}));
            return this;
        }
    });

    return views;
});
