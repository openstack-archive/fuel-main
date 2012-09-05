define(
[
    'models',
    'text!templates/dialogs/create_cluster.html',
],
function(models, createClusterDialogTemplate) {
    var views = {}

    views.createClusterDialog = Backbone.View.extend({
        className: 'modal fade',
        template: _.template(createClusterDialogTemplate),
        events: {
            'click .create-cluster-btn': 'createCluster',
            'keydown input': 'onInputKeydown',
            'click .dialog-node': 'toggleNode'
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
                    this.model.fetch();
                }, this)});
                this.$el.modal('hide');
            }
        },
        onInputKeydown: function(e) {
            if (e.which == 13) this.createCluster();
        },
        toggleNode: function(e) {
            $(e.currentTarget).toggleClass('node-checked').toggleClass('node-unchecked');
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

    return views;
});
