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
    'require',
    'utils',
    'models',
    'text!templates/dialogs/simple_message.html',
    'text!templates/dialogs/create_cluster.html',
    'text!templates/dialogs/rhel_license.html',
    'text!templates/dialogs/change_cluster_mode.html',
    'text!templates/dialogs/discard_changes.html',
    'text!templates/dialogs/display_changes.html',
    'text!templates/dialogs/remove_cluster.html',
    'text!templates/dialogs/error_message.html',
    'text!templates/dialogs/show_node.html',
    'text!templates/dialogs/dismiss_settings.html'
],
function(require, utils, models, simpleMessageTemplate, createClusterDialogTemplate, rhelCredentialsDialogTemplate, changeClusterModeDialogTemplate, discardChangesDialogTemplate, displayChangesDialogTemplate, removeClusterDialogTemplate, errorMessageTemplate, showNodeInfoTemplate, discardSettingsChangesTemplate) {
    'use strict';

    var views = {};

    views.Dialog = Backbone.View.extend({
        className: 'modal fade',
        errorMessageTemplate: _.template(errorMessageTemplate),
        modalBound: false,
        beforeTearDown: function() {
            this.$el.modal('hide');
        },
        displayErrorMessage: function () {
            var logsLink;
            try {
                if (app.page.model.constructor == models.Cluster) {
                    var options = {type: 'local', source: 'nailgun', level: 'error'};
                    logsLink = '#cluster/' + app.page.model.id + '/logs/' + utils.serializeTabOptions(options);
                }
            } catch(e) {}
            this.$('.modal-body').html(this.errorMessageTemplate({logsLink: logsLink}));
        },
        displayInfoMessage: function(options) {
            this.template = _.template(simpleMessageTemplate);
            this.render(options);
            if (options.error) {
                this.displayErrorMessage();
            }
        },
        initialize: function(options) {
            _.defaults(this, options);
        },
        render: function(options) {
            this.$el.attr('tabindex', -1);
            this.$el.html(this.template(options));
            if (!this.modalBound) {
                this.$el.on('hidden', _.bind(this.tearDown, this));
                this.$el.on('shown', _.bind(function() {
                    this.$('[autofocus]:first').focus();
                }, this));
                this.$el.modal();
                this.modalBound = true;
            }
            return this;
        }
    });

    views.DialogWithRhelCredentials = views.Dialog.extend({
        displayRhelCredentialsForm: function() {
            this.$('.credentials').html('');
            if (this.release.get('state') == 'not_available' || this.release.get('state') == 'error') {
                var commonViews = require('views/common'); // avoid circular dependencies
                this.rhelCredentialsForm = new commonViews.RhelCredentialsForm({dialog: this});
                this.registerSubView(this.rhelCredentialsForm);
                this.$('.credentials').append(this.rhelCredentialsForm.render().el);
            }
        }
    });

    views.CreateClusterDialog = views.DialogWithRhelCredentials.extend({
        template: _.template(createClusterDialogTemplate),
        events: {
            'click .create-cluster-btn:not(:disabled)': 'applyRhelCredentials',
            'keydown input': 'onInputKeydown',
            'change select[name=release]': 'updateReleaseParameters'
        },
        applyRhelCredentials: function() {
            if (this.release.get('state') == 'not_available') {
                var deferred = this.rhelCredentialsForm.applyCredentials();
                if (deferred) {
                    this.$('.create-cluster-btn').attr('disabled', true);
                    deferred
                        .done(_.bind(function(response) {
                            this.release.fetch()
                                .always(_.bind(function() {
                                    this.displayRhelCredentialsForm();
                                    this.createCluster();
                                }, this));
                        }, this))
                        .fail(_.bind(function(response) {
                            if (response.status == 400) {
                                this.$('.create-cluster-btn').attr('disabled', false);
                            }
                        }, this));
                }
            } else {
                this.createCluster();
            }
        },
        createCluster: function() {
            this.$('.control-group').removeClass('error').find('.help-inline').text('');
            var cluster = new models.Cluster();
            cluster.on('invalid', function(model, error) {
                _.each(error, function(message, field) {
                    this.$('*[name=' + field + ']').closest('.control-group').addClass('error').find('.help-inline').text(message);
                }, this);
                this.$('.create-cluster-btn').attr('disabled', false);
            }, this);
            var deferred = cluster.save({
                name: $.trim(this.$('input[name=name]').val()),
                release: parseInt(this.$('select[name=release]').val(), 10)
            });
            if (deferred) {
                this.$('.create-cluster-btn').attr('disabled', true);
                deferred
                    .done(_.bind(function() {
                        this.$el.modal('hide');
                        this.collection.add(cluster);
                    }, this))
                    .fail(_.bind(function(response) {
                        if (response.status == 409) {
                            cluster.trigger('invalid', cluster, {name: response.responseText});
                            this.$('.create-cluster-btn').attr('disabled', false);
                        } else if (response.status == 400) {
                            this.displayInfoMessage({error: false, title: 'Create a new OpenStack environment error', message: response.responseText});
                        } else {
                            this.displayErrorMessage();
                        }
                    }, this));
            }
        },
        onInputKeydown: function(e) {
            this.$('.control-group.error').removeClass('error');
            this.$('.help-inline').html('');
            if (e.which == 13) {
                this.applyRhelCredentials();
            }
        },
        updateReleaseParameters: function() {
            if (this.releases.length) {
                var releaseId = parseInt(this.$('select[name=release]').val(), 10);
                this.release = this.releases.get(releaseId);
                this.$('.rhel-license').toggle(this.release.get('state') == 'not_available');
                this.$('.release-description').text(this.release.get('description'));
                this.displayRhelCredentialsForm();
            }
        },
        renderReleases: function(e) {
            var input = this.$('select[name=release]');
            input.html('');
            this.releases.each(function(release) {
                input.append($('<option/>').attr('value', release.id).text(release.get('name') + ' (' + release.get('version') + ')'));
            });
            this.updateReleaseParameters();
        },
        initialize: function() {
            this.releases = new models.Releases();
            this.releases.fetch().done(_.bind(this.renderReleases, this));
        },
        render: function() {
            this.tearDownRegisteredSubViews();
            this.constructor.__super__.render.call(this);
            return this;
        }
    });

    views.RhelCredentialsDialog = views.DialogWithRhelCredentials.extend({
        template: _.template(rhelCredentialsDialogTemplate),
        events: {
            'click .btn-os-download': 'applyRhelCredentials'
        },
        applyRhelCredentials: function() {
            var deferred = this.rhelCredentialsForm.applyCredentials();
            if (deferred) {
                this.$('.btn-os-download').addClass('disabled');
                deferred
                    .done(_.bind(function() {
                        app.page.tasks.fetch().done(_.bind(function() {
                            this.$el.modal('hide');
                            app.page.scheduleUpdate();
                        }, this));
                    }, this))
                    .fail(_.bind(function(response) {
                        if (response.status == 400) {
                            this.$('.btn-os-download').removeClass('disabled');
                        }
                    }, this));
            } else {
                this.$('.btn-os-download').removeClass('disabled');
            }
        },
        render: function() {
            this.tearDownRegisteredSubViews();
            this.constructor.__super__.render.call(this);
            this.displayRhelCredentialsForm();
            return this;
        }
    });

    views.ChangeClusterModeDialog = views.Dialog.extend({
        template: _.template(changeClusterModeDialogTemplate),
        events: {
            'change input[name=mode]': 'toggleTypes',
            'click .apply-btn:not(.disabled)': 'apply'
        },
        apply: function() {
            var cluster = this.model;
            var mode = this.$('input[name=mode]:checked').val();
            if (cluster.get('mode') == mode) {
                this.$el.modal('hide');
            } else {
                this.$('.apply-btn').addClass('disabled');
                cluster.save({mode: mode}, {patch: true, wait: true}).fail(_.bind(this.displayErrorMessage, this));
            }
        },
        toggleTypes: function() {
            this.$('.mode-description').addClass('hide');
            this.$('.help-mode-' + this.$('input[name=mode]:checked').val()).removeClass('hide');
        },
        render: function() {
            this.constructor.__super__.render.call(this, {cluster: this.model});
            this.toggleTypes();
            return this;
        }
    });

    views.DiscardChangesDialog = views.Dialog.extend({
        template: _.template(discardChangesDialogTemplate),
        events: {
            'click .discard-btn:not(.disabled)': 'discardChanges'
        },
        discardChanges: function() {
            this.$('.discard-btn').addClass('disabled');
            var pendingNodes = this.model.get('nodes').filter(function(node) {
                return node.get('pending_addition') || node.get('pending_deletion');
            });
            var nodes = new models.Nodes(pendingNodes);
            nodes.each(function(node) {
                if (node.get('pending_addition')) {
                    node.set({
                        cluster_id: null,
                        role: null,
                        pending_addition: false
                    }, {silent: true});
                } else {
                    node.set({pending_deletion: false}, {silent: true});
                }
            });
            nodes.toJSON = function() {
                return this.map(function(node) {
                    return _.pick(node.attributes, 'id', 'cluster_id', 'role', 'pending_addition', 'pending_deletion');
                });
            };
            Backbone.sync('update', nodes)
                .done(_.bind(function() {
                    this.$el.modal('hide');
                    this.model.get('nodes').fetch({data: {cluster_id: this.model.id}});
                    // we set node flags silently, so trigger resize event to redraw node list
                    this.model.get('nodes').trigger('resize');
                    app.navbar.refresh();
                }, this))
                .fail(_.bind(this.displayErrorMessage, this));
        },
        render: function() {
            this.constructor.__super__.render.call(this, {cluster: this.model});
            return this;
        }
    });

    views.DisplayChangesDialog = views.Dialog.extend({
        template: _.template(displayChangesDialogTemplate),
        events: {
            'click .start-deployment-btn:not(.disabled)': 'deployCluster'
        },
        deployCluster: function() {
            this.$('.start-deployment-btn').addClass('disabled');
            var task = new models.Task();
            task.save({}, {url: _.result(this.model, 'url') + '/changes', type: 'PUT'})
                .done(_.bind(function() {
                    this.$el.modal('hide');
                    app.page.deploymentStarted();
                }, this))
                .fail(_.bind(this.displayErrorMessage, this));
        },
        render: function() {
            this.constructor.__super__.render.call(this, {
                cluster: this.model,
                size: this.model.get('mode') == 'ha' ? 3 : 1
            });
            return this;
        }
    });

    views.RemoveClusterDialog = views.Dialog.extend({
        template: _.template(removeClusterDialogTemplate),
        events: {
            'click .remove-cluster-btn:not(.disabled)': 'removeCluster'
        },
        removeCluster: function() {
            this.$('.remove-cluster-btn').addClass('disabled');
            this.model.destroy({wait: true})
                .done(_.bind(function() {
                    this.$el.modal('hide');
                    app.navbar.refresh();
                    app.navigate('#clusters', {trigger: true});
                }, this))
                .fail(_.bind(this.displayErrorMessage, this));
        },
        render: function() {
            this.constructor.__super__.render.call(this, {cluster: this.model});
            return this;
        }
    });

    views.ShowNodeInfoDialog = views.Dialog.extend({
        template: _.template(showNodeInfoTemplate),
        templateHelpers: {
            showPropertyName: function(propertyName) {
                return propertyName.replace(/_/g, ' ');
            },
            showPropertyValue: function(group, name, value) {
                try {
                    if (group == 'memory' && (name == 'total' || name == 'maximum_capacity' || name == 'size')) {
                        value = utils.showMemorySize(value);
                    } else if (group == 'disks' && name == 'size') {
                        value = utils.showDiskSize(value);
                    } else if (name == 'size') {
                        value = utils.showSize(value);
                    } else if (name == 'frequency') {
                        value = utils.showFrequency(value);
                    } else if (name == 'max_speed' || name == 'current_speed') {
                        value = utils.showBandwidth(value);
                    }
                } catch (e) {}
                return value;
            },
            showSummary: function(meta, group) {
                var summary = '';
                try {
                    if (group == 'system') {
                        summary = (meta.system.manufacturer || '') + ' ' + (meta.system.product || '');
                    } else if (group == 'memory') {
                        if (_.isArray(meta.memory.devices) && meta.memory.devices.length) {
                            var sizes = _.groupBy(_.pluck(meta.memory.devices, 'size'), utils.showMemorySize);
                            summary = _.map(_.keys(sizes).sort(), function(size) {return sizes[size].length + ' x ' + size;}).join(', ');
                            summary += ', ' + utils.showMemorySize(meta.memory.total) + ' total';
                        } else {
                            summary = utils.showMemorySize(meta.memory.total) + ' total';
                        }
                    } else if (group == 'disks') {
                        summary = meta.disks.length + ' drive';
                        summary += meta.disks.length == 1 ? ', ' : 's, ';
                        summary += utils.showDiskSize(_.reduce(_.pluck(meta.disks, 'size'), function(sum, n) {return sum + n;}, 0)) + ' total';
                    } else if (group == 'cpu') {
                        var frequencies = _.groupBy(_.pluck(meta.cpu.spec, 'frequency'), utils.showFrequency);
                        summary = _.map(_.keys(frequencies).sort(), function(frequency) {return frequencies[frequency].length + ' x ' + frequency;}).join(', ');
                    } else if (group == 'interfaces') {
                        var bandwidths = _.groupBy(_.pluck(meta.interfaces, 'current_speed'), utils.showBandwidth);
                        summary = _.map(_.keys(bandwidths).sort(), function(bandwidth) {return bandwidths[bandwidth].length + ' x ' + bandwidth;}).join(', ');
                    }
                } catch (e) {}
                return summary;
            },
            sortEntryProperties: function(entry) {
                var properties = _.keys(entry);
                if (_.has(entry, 'name')) {
                    properties = ['name'].concat(_.keys(_.omit(entry, 'name')));
                }
                return properties;
            }
        },
        events: {
            'click .accordion-heading': 'toggle',
            'click .btn-edit-disks': 'goToDisksConfiguration',
            'click .btn-edit-networks': 'goToInterfacesConfiguration'
        },
        toggle: function(e) {
            $(e.currentTarget).siblings('.accordion-body').collapse('toggle');
        },
        goToDisksConfiguration: function() {
            app.navigate('#cluster/' + this.clusterId + '/nodes/disks/' + this.node.id, {trigger: true});
        },
        goToInterfacesConfiguration: function() {
            app.navigate('#cluster/' + this.clusterId + '/nodes/interfaces/' + this.node.id, {trigger: true});
        },
        initialize: function(options) {
            _.defaults(this, options);
            this.node.on('sync', this.render, this);
        },
        render: function() {
            this.constructor.__super__.render.call(this, _.extend({
                node: this.node,
                configurationPossible: this.configurationPossible
            }, this.templateHelpers));
            this.$('.accordion-body').collapse({
                parent: this.$('.accordion'),
                toggle: false
            }).on('show', function(e) {
                $(e.currentTarget).siblings('.accordion-heading').find('i').removeClass('icon-expand').addClass('icon-collapse');
            }).on('hide', function(e) {
                $(e.currentTarget).siblings('.accordion-heading').find('i').removeClass('icon-collapse').addClass('icon-expand');
            }).on('hidden', function(e) {
                e.stopPropagation();
            });
            return this;
        }
    });

    views.DiscardSettingsChangesDialog = views.Dialog.extend({
        template: _.template(discardSettingsChangesTemplate),
        defaultMessage: 'Settings were modified but not saved. Do you want to discard your changes and leave the page?',
        verificationMessage: 'Network verification is in progress. You should save changes or stay on the tab.',
        events: {
            'click .proceed-btn': 'proceed'
        },
        proceed: function() {
            this.$el.modal('hide');
            app.page.removeVerificationTask().always(_.bind(this.cb, this));
        },
        render: function() {
            if (this.verification) {
                this.message = this.verificationMessage;
            }
            this.constructor.__super__.render.call(this, {
                message: this.message || this.defaultMessage,
                verification: this.verification || false
            });
            return this;
        }
    });

    return views;
});
