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
            'keydown input': 'onInputKeydown'
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
                release: this.$('select[name=release]').val()
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
            'change input[name=mode]': 'toggleRedundancyInput',
            'click .apply-btn': 'apply'
        },
        apply: function() {
            var cluster = this.model;
            cluster.set({
                mode: this.$('input[name=mode]:checked').val(),
                redundancy: parseInt(this.$('input[name=redundancy]').val(), 10)
            });
            if (cluster.get('mode') != 'ha') cluster.unset('redundancy');
            cluster.update(['mode', 'redundancy']);
            this.$el.modal('hide');
        },
        toggleRedundancyInput: function() {
            this.$('.redundancy-control-group').toggleClass('hide', this.$('input[name=mode]:checked').val() != 'ha');
        },
        render: function() {
            this.constructor.__super__.render.call(this, {cluster: this.model});
            this.toggleRedundancyInput();
        }
    });

    views.changeClusterTypeDialog = views.dialog.extend({
        template: _.template(changeClusterTypeDialogTemplate),
        events: {
            'click .apply-btn': 'apply'
        },
        apply: function() {
            this.model.update({type: this.$('input[name=type]:checked').val()});
            this.$el.modal('hide');
        },
        render: function() {
            this.constructor.__super__.render.call(this, {cluster: this.model});
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
