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
    'models',
    'views/common',
    'views/dialogs',
    'text!templates/cluster/actions_tab.html'
],
function(models, commonViews, dialogViews, actionsTabTemplate) {
    'use strict';

    var ActionsTab = commonViews.Tab.extend({
        template: _.template(actionsTabTemplate),
        events: {
            'click .rename-cluster-form .apply-name-btn': 'applyNewClusterName',
            'keydown .rename-cluster-form input': 'onClusterNameInputKeydown',
            'click .delete-cluster-form .delete-cluster-btn': 'deleteCluster'
        },
        applyNewClusterName: function() {
            var name = $.trim(this.$('.rename-cluster-form input').val());
            if (name != this.model.get('name')) {
                var deferred = this.model.save({name: name}, {patch: true, wait: true});
                if (deferred) {
                    var controls = this.$('.rename-cluster-form input, .rename-cluster-form button');
                    controls.attr('disabled', true);
                    deferred
                        .fail(_.bind(function(response) {
                            if (response.status == 409) {
                                this.model.trigger('invalid', this.model, {name: response.responseText});
                            }
                        }, this))
                        .always(_.bind(function() {
                            controls.attr('disabled', false);
                        }, this));
                }
            }
        },
        showValidationError: function(model, error) {
            this.$('.alert-error').text(_.values(error).join('; ')).show();
        },
        onClusterNameInputKeydown: function(e) {
            this.$('.alert-error').hide();
        },
        deleteCluster: function() {
            var deleteClusterDialogView = new dialogViews.RemoveClusterDialog({model: this.model});
            this.registerSubView(deleteClusterDialogView);
            deleteClusterDialogView.render();
        },
        initialize: function(options) {
            _.defaults(this, options);
            this.model.on('change:name', this.render, this);
            this.model.on('invalid', this.showValidationError, this);
        },
        render: function() {
            this.$el.html(this.template({cluster: this.model}));
            return this;
        }
    });

    return ActionsTab;
});
