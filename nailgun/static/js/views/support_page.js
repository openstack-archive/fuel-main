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
        template: _.template(supportPageTemplate),
        events: {
            'click .download-logs:not(.disabled)': 'downloadLogs'
        },
        downloadLogs: function() {
            this.$('.download-logs').addClass('disabled');
            window.location = '/api/logs/package';
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
