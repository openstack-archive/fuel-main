define(
[
    'models',
    'text!templates/dialogs/create_cluster.html',
    'text!templates/dialogs/change_cluster_mode.html',
    'text!templates/dialogs/change_cluster_type.html',
    'text!templates/dialogs/change_network_settings.html'
],
function(models, createClusterDialogTemplate, changeClusterModeDialogTemplate, changeClusterTypeDialogTemplate, changeNetworkSettingsDialogTemplate) {
    'use strict';

    var views = {};

    views.Dialog = Backbone.View.extend({
        className: 'modal fade',
        modalBound: false,
        render: function(options) {
            this.$el.html(this.template(options));
            if (!this.modalBound) {
                this.$el.on('hidden', function() {$(this).remove();});
                this.$el.modal();
                this.modelBound = true;
            }
            return this;
        }
    });

    views.CreateClusterDialog = views.Dialog.extend({
        template: _.template(createClusterDialogTemplate),
        events: {
            'click .create-cluster-btn': 'createCluster',
            'keydown input': 'onInputKeydown',
            'change select[name=release]': 'updateReleaseDescription'
        },
        createCluster: function() {
            this.$('.help-inline').text('');
            this.$('.control-group').removeClass('error');
            var cluster = new models.Cluster();
            cluster.on('error', function(model, error) {
                _.each(error, function(message, field) {
                    this.$('*[name=' + field + '] ~ .help-inline').text(message);
                    this.$('*[name=' + field + ']').closest('.control-group').addClass('error');
                }, this);
            }, this);
            cluster.set({
                name: this.$('input[name=name]').val(),
                release: parseInt(this.$('select[name=release]').val(), 10)
            });
            if (cluster.isValid()) {
                cluster.save({}, {success: _.bind(function() {
                    this.collection.fetch();
                }, this)});
                this.$el.modal('hide');
            }
        },
        onInputKeydown: function(e) {
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
            this.releases.bind('reset', this.renderReleases, this);
        }
    });

    views.ChangeClusterModeDialog = views.Dialog.extend({
        template: _.template(changeClusterModeDialogTemplate),
        events: {
            'change input[name=mode]': 'toggleControls',
            'click .apply-btn': 'apply'
        },
        apply: function() {
            var cluster = this.model;
            var valid = true;
            cluster.on('error', function(model, errors) {
                valid = false;
                _.each(errors, function(message, field) {
                    this.$('*[name=' + field + '] ~ .help-inline').text(message);
                    this.$('*[name=' + field + ']').closest('.control-group').addClass('error');
                }, this);
            }, this);
            var mode = this.$('input[name=mode]:checked').val();
            var redundancy = mode == 'ha' ? parseInt(this.$('input[name=redundancy]').val(), 10) : null;
            cluster.set({mode: mode, redundancy: redundancy});
            if (valid) {
                cluster.update(['mode', 'redundancy']);
                this.$el.modal('hide');
            }
        },
        toggleControls: function() {
            this.$('.redundancy-control-group').toggleClass('hide', this.$('input[name=mode]:checked').val() != 'ha');
            this.$('.help-block').addClass('hide');
            this.$('.help-mode-' + this.$('input[name=mode]:checked').val()).removeClass('hide');
        },
        render: function() {
            this.constructor.__super__.render.call(this, {cluster: this.model});
            this.toggleControls();
            return this;
        }
    });

    views.ChangeClusterTypeDialog = views.Dialog.extend({
        template: _.template(changeClusterTypeDialogTemplate),
        events: {
            'change input[name=type]': 'toggleDescription',
            'click .apply-btn': 'apply'
        },
        apply: function() {
            this.model.update({type: this.$('input[name=type]:checked').val()});
            this.$el.modal('hide');
        },
        toggleDescription: function() {
            this.$('.help-block').addClass('hide');
            this.$('.help-type-' + this.$('input[name=type]:checked').val()).removeClass('hide');
        },
        render: function() {
            this.constructor.__super__.render.call(this, {cluster: this.model});
            this.toggleDescription();
            return this;
        }
    });

    views.ChangeNetworkSettingsDialog = views.Dialog.extend({
        template: _.template(changeNetworkSettingsDialogTemplate),
        events: {
            'click .apply-btn': 'apply'
        },
        apply: function() {
            var valid = true;
            this.$('.help-inline').text('');
            this.$('.control-group').removeClass('error');
            this.networks.each(function(network) {
                var row = this.$('.control-group[data-network-name=' + network.get('name') + ']');
                network.on('error', function(model, errors) {
                    valid = false;
                    $('.network-error .help-inline', row).text(errors.cidr || errors.vlan_id);
                    row.addClass('error');
                }, this);
                network.set({
                    cidr: $('.network-cidr input', row).val(),
                    vlan_id: parseInt($('.network-vlan input', row).val(), 10)
                });
            }, this);
            if (valid) {
                Backbone.sync('update', this.networks);
                this.$el.modal('hide');
            }
        },
        initialize: function(options) {
            this.networks = new models.Networks();
            this.networks.deferred = this.networks.fetch({data: {cluster_id: this.model.id}});
            this.networks.bind('reset', this.render, this);
        },
        render: function() {
            return this.constructor.__super__.render.call(this, {cluster: this.model, networks: this.networks});
        }
    });

    return views;
});
