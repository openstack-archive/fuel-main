define(
[
    'models',
    'text!templates/dialogs/create_cluster.html',
    'text!templates/dialogs/change_cluster_mode.html',
    'text!templates/dialogs/change_cluster_type.html',
    'text!templates/dialogs/change_network_mode.html',
    'text!templates/dialogs/change_network_parameters.html'
],
function(models, createClusterDialogTemplate, changeClusterModeDialogTemplate, changeClusterTypeDialogTemplate, changeNetworkModeDialogTemplate, changeNetworkParametersDialogTemplate) {
    var views = {}

    views.dialog = Backbone.View.extend({
        className: 'modal fade',
        render: function(options) {
            this.$el.html(this.template(options));
            this.$el.on('hidden', function() {$(this).remove()});
            this.$el.modal();
            return this;
        }
    })

    views.createClusterDialog = views.dialog.extend({
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
            if (e.which == 13) this.createCluster();
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
        },
        render: function() {
            this.constructor.__super__.render.call(this);
            this.renderReleases();
            this.releases.bind('reset', this.renderReleases, this);
            return this;
        }
    });

    views.changeClusterModeDialog = views.dialog.extend({
        template: _.template(changeClusterModeDialogTemplate),
        events: {
            'change input[name=mode]': 'toggleControls',
            'click .apply-btn': 'apply'
        },
        apply: function() {
            var cluster = this.model;
            var valid = true;
            cluster.on('error', function(model, error) {
                valid = false;
                _.each(error, function(message, field) {
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
        }
    });

    views.changeClusterTypeDialog = views.dialog.extend({
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
        }
    });

    views.changeNetworkModeDialog = views.dialog.extend({
        template: _.template(changeNetworkModeDialogTemplate)
    });

    views.changeNetworkParametersDialog = views.dialog.extend({
        template: _.template(changeNetworkParametersDialogTemplate)
    });

    return views;
});
