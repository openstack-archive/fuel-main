define(
[
    'models',
    'text!templates/dialogs/simple_message.html',
    'text!templates/dialogs/create_cluster.html',
    'text!templates/dialogs/change_cluster_mode.html',
    'text!templates/dialogs/discard_changes.html',
    'text!templates/dialogs/display_changes.html',
    'text!templates/dialogs/remove_cluster.html',
    'text!templates/dialogs/error_message.html',
    'text!templates/dialogs/show_node.html',
    'text!templates/dialogs/dismiss_settings.html'
],
function(models, simpleMessageTemplate, createClusterDialogTemplate, changeClusterModeDialogTemplate, discardChangesDialogTemplate, displayChangesDialogTemplate, removeClusterDialogTemplate, errorMessageTemplate, showNodeInfoTemplate, disacardSettingsChangesTemplate) {
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
                    logsLink = '#cluster/' + app.page.model.id + '/logs/' + app.serializeTabOptions(options);
                }
            } catch(e) {}
            this.$('.modal-body').html(this.errorMessageTemplate({logsLink: logsLink}));
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

    views.SimpleMessage = views.Dialog.extend({
        template: _.template(simpleMessageTemplate),
        render: function() {
            this.constructor.__super__.render.call(this, {title: this.title, message: this.message});
            if (this.error) {
                this.displayErrorMessage();
            }
            return this;
        }
    });

    views.CreateClusterDialog = views.Dialog.extend({
        template: _.template(createClusterDialogTemplate),
        events: {
            'click .create-cluster-btn:not(.disabled)': 'createCluster',
            'keydown input': 'onInputKeydown',
            'change select[name=release]': 'updateReleaseDescription'
        },
        createCluster: function() {
            this.$('.control-group').removeClass('error').find('.help-inline').text('');
            var cluster = new models.Cluster();
            cluster.on('invalid', function(model, error) {
                _.each(error, function(message, field) {
                    this.$('*[name=' + field + ']').closest('.control-group').addClass('error').find('.help-inline').text(message);
                }, this);
            }, this);
            var deferred = cluster.save({
                name: $.trim(this.$('input[name=name]').val()),
                release: parseInt(this.$('select[name=release]').val(), 10)
            });
            if (deferred) {
                this.$('.create-cluster-btn').addClass('disabled');
                deferred
                    .done(_.bind(function() {
                        this.$el.modal('hide');
                        this.collection.fetch();
                    }, this))
                    .fail(_.bind(function(response) {
                        if (response.status == 409) {
                            cluster.trigger('invalid', cluster, {name: response.responseText});
                            this.$('.create-cluster-btn').removeClass('disabled');
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
                this.createCluster();
            }
        },
        renderReleases: function(e) {
            var input = this.$('select[name=release]');
            input.html('');
            this.releases.each(function(release) {
                input.append($('<option/>').attr('value', release.id).text(release.get('name')));
            }, this);
            this.updateReleaseDescription();
        },
        updateReleaseDescription: function() {
            if (this.releases.length) {
                var releaseId = parseInt(this.$('select[name=release]').val(), 10);
                var release = this.releases.get(releaseId);
                this.$('select[name=release] ~ .help-block').text(release.get('description'));
            }
        },
        initialize: function() {
            this.releases = new models.Releases();
            this.releases.fetch();
            this.releases.bind('sync', this.renderReleases, this);
        }
    });

    views.ChangeClusterModeDialog = views.Dialog.extend({
        template: _.template(changeClusterModeDialogTemplate),
        events: {
            'change input[name=mode]': 'toggleTypes',
            /*'change input[name=type]': 'toggleTypeDescription',*/
            'click .apply-btn:not(.disabled)': 'apply'
        },
        apply: function() {
            var cluster = this.model;
            var mode = this.$('input[name=mode]:checked').val();
            var type = this.$('input[name=type]:checked').val();
            if (cluster.get('mode') == mode && cluster.get('type') == type) {
                this.$el.modal('hide');
            } else {
                this.$('.apply-btn').addClass('disabled');
                cluster.save({mode: mode, type: type}, {patch: true, wait: true}).fail(_.bind(this.displayErrorMessage, this));
            }
        },
        toggleTypes: function() {
            //this.$('.type-control-group, .simple-type-title, .label-info').toggleClass('hide', this.$('input[name=mode]:checked').val() == 'singlenode');
            this.$('.mode-description').addClass('hide');
            this.$('.help-mode-' + this.$('input[name=mode]:checked').val()).removeClass('hide');
        },
        toggleTypeDescription: function() {
            this.$('.type-description').addClass('hide');
            this.$('.help-type-' + this.$('input[name=type]:checked').val()).removeClass('hide');
        },
        render: function() {
            this.constructor.__super__.render.call(this, {cluster: this.model});
            this.toggleTypes();
            this.toggleTypeDescription();
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
                    this.model.get('nodes').fetch({data: {cluster_id: this.model.id}, reset: true});
                    app.navbar.nodes.fetch();
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
                    app.navbar.notifications.fetch();
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
        events: {
            'click .accordion-heading': 'toggle'
        },
        toggle: function(e) {
            $(e.currentTarget).siblings('.accordion-body').collapse('toggle');
        },
        render: function() {
            this.constructor.__super__.render.call(this, {node: this.node});
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
        template: _.template(disacardSettingsChangesTemplate),
        defaultMessage: 'Settings were modified but not saved. Changes will be lost. Do you want to proceed?',
        events: {
            'click .proceed-btn': 'proceed'
        },
        proceed: function() {
            this.$el.modal('hide');
            app.page.removeVerificationTask().done(_.bind(this.cb, this));
        },
        render: function() {
            this.constructor.__super__.render.call(this, {
                message: this.message || this.defaultMessage
            });
            return this;
        }
    });

    return views;
});
