define(
[
    'models',
    'text!templates/dialogs/create_cluster.html',
    'text!templates/dialogs/change_network_mode.html',
    'text!templates/dialogs/change_network_parameters.html'
],
function(models, createClusterDialogTemplate, changeNetworkModeDialogTemplate, changeNetworkParametersDialogTemplate) {
    var views = {}

    views.createClusterDialog = Backbone.View.extend({
        className: 'modal fade',
        template: _.template(createClusterDialogTemplate),
        events: {
            'click .create-cluster-btn': 'createCluster',
            'keydown input': 'onInputKeydown',
            'change input[name=mode]': 'toggleRedundancyInput'
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
                release: this.$('select[name=release]').val(),
                type: this.$('input[name=type]:checked').val(),
                mode: this.$('input[name=mode]:checked').val(),
                redundancy: parseInt(this.$('input[name=redundancy]').val(), 10)
            });
            if (cluster.isValid()) {
                if (cluster.get('mode') != 'ha') cluster.unset('redundancy');
                cluster.save({}, {success: _.bind(function() {
                    this.collection.fetch();
                }, this)});
                this.$el.modal('hide');
            }
        },
        toggleRedundancyInput: function() {
            this.$('.redundancy-control-group').toggleClass('hide', this.$('input[name=mode]:checked').val() != 'ha');
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
            this.$el.html(this.template());
            this.$el.on('hidden', function() {$(this).remove()});
            this.$el.modal();

            this.renderReleases();
            this.releases.bind('reset', this.renderReleases, this);

            return this;
        }
    });

    views.changeNetworkModeDialog = Backbone.View.extend({
        className: 'modal fade',
        template: _.template(changeNetworkModeDialogTemplate),
        events: {
        },
        render: function() {
            this.$el.html(this.template());
            this.$el.on('hidden', function() {$(this).remove()});
            this.$el.modal();
            return this;
        }
    });

    views.changeNetworkParametersDialog = Backbone.View.extend({
        className: 'modal fade',
        template: _.template(changeNetworkParametersDialogTemplate),
        events: {
        },
        render: function() {
            this.$el.html(this.template());
            this.$el.on('hidden', function() {$(this).remove()});
            this.$el.modal();
            return this;
        }
    });

    return views;
});
