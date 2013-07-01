define(
[
    'models',
    'views/common',
    'views/dialogs',
    'text!templates/cluster/healthcheck_tab.html'
],
function(models, commonViews, dialogViews, healthcheckTabTemplate) {
    'use strict';

    var HealthCheckTab = commonViews.Tab.extend({
        template: _.template(healthcheckTabTemplate),
        events: {
        },
        initialize: function(options) {
            _.defaults(this, options);
        },
        render: function() {
            this.$el.html(this.template({cluster: this.model}));
            return this;
        }
    });

    return HealthCheckTab;
});
