define(
[
    'models',
    'text!templates/dialogs/add_remove_nodes.html',
    'text!templates/dialogs/create_cluster.html',
    'text!templates/dialogs/node_list.html',
    'text!templates/dialogs/assign_roles.html',
    'text!templates/dialogs/deployment_type_list.html'
],
function(models, addRemoveNodesDialogTemplate, createClusterDialogTemplate, nodeDialogNodeListTemplate, assignRolesDialogTemplate, deploymentTypeListTemplate) {
    var views = {}

    views.addRemoveNodesDialog = Backbone.View.extend({
        className: 'modal fade',
        template: _.template(addRemoveNodesDialogTemplate),
        events: {
            'click .save-changes-btn': 'saveChanges',
            'click .dialog-node': 'toggleNode'
        },
        saveChanges: function(e) {
            var nodes = this.$('.node-checked').map(function(){return $(this).attr('data-node-id')}).get();
            this.model.update({nodes: nodes});
            this.$el.modal('hide');
        },
        toggleNode: function(e) {
            $(e.currentTarget).toggleClass('node-checked').toggleClass('node-unchecked');
        },
        initialize: function() {
            this.availableNodes = new models.Nodes();
            this.availableNodes.fetch({data: {cluster_id: ''}});
        },
        render: function() {
            this.$el.html(this.template());
            this.$el.on('hidden', function() {$(this).remove()});
            this.$el.modal();

            this.$('.cluster-nodes').html(new views.nodeList({model: this.model.get('nodes'), checked: true}).render().el);
            this.$('.available-nodes').html(new views.nodeList({model: this.availableNodes, checked: false}).render().el);
            return this;
        }
    });

    views.createClusterDialog = Backbone.View.extend({
        className: 'modal fade',
        template: _.template(createClusterDialogTemplate),
        events: {
            'click .create-cluster-btn': 'createCluster',
            'click .dialog-node': 'toggleNode'
        },
        createCluster: function(e) {
            this.$('.help-inline').text('');
            this.$('.control-group').removeClass('error');
            var nodes = this.$('.node-checked').map(function(){return $(this).attr('data-node-id')}).get();
            var cluster = new models.Cluster();
            cluster.on('error', function(model, error) {
                _.each(error, function(message, field) {
                    this.$('*[name=' + field + '] ~ .help-inline').text(message);
                    this.$('*[name=' + field + ']').closest('.control-group').addClass('error');
                }, this);
            }, this);
            cluster.set({
                name: this.$('input[name=name]').attr('value'),
                release: this.$('select[name=release]').attr('value'),
                nodes: nodes
            });
            if (cluster.isValid()) {
                cluster.save({}, {success: _.bind(function() {
                    this.model.fetch();
                }, this)});
                this.$el.modal('hide');
            }
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
            this.availableNodes = new models.Nodes();
            this.availableNodes.fetch({data: {cluster_id: ''}});
        },
        render: function() {
            this.$el.html(this.template());
            this.$el.on('hidden', function() {$(this).remove()});
            this.$el.modal();

            this.renderReleases();
            this.releases.bind('reset', this.renderReleases, this);

            this.$('.available-nodes').html(new views.nodeList({model: this.availableNodes, checked: false}).render().el);

            return this;
        }
    });

    views.nodeList = Backbone.View.extend({
        template: _.template(nodeDialogNodeListTemplate),
        initialize: function(options) {
            this.checked = options.checked;
            this.model.bind('reset', this.render, this);
        },
        render: function() {
            this.$el.html(this.template({nodes: this.model, checked: this.checked}));
            return this;
        }
    });

    views.assignRolesDialog = Backbone.View.extend({
        className: 'modal fade',
        template: _.template(assignRolesDialogTemplate),
        events: {
            'click .assign-roles-btn': 'assignRoles'
        },
        assignRoles: function() {
            var selectedDeploymentTypeId = this.$('input[name=type]:checked').attr('value');
            var deploymentType = new models.DeploymentType({cluster: this.model, id: selectedDeploymentTypeId});
            deploymentType.save({}, {
                success: _.bind(function() {
                    this.model.fetch();
                }, this)
            });
            this.$el.modal('hide');
        },
        initialize: function() {
            this.deploymentTypes = new models.DeploymentTypes();
            this.deploymentTypes.cluster = this.model;
            this.deploymentTypes.fetch();
        },
        render: function() {
            this.$el.html(this.template());
            this.$el.on('hidden', function() {$(this).remove()});
            this.$el.modal();

            this.$('form').html(new views.deploymentTypeList({model: this.deploymentTypes}).render().el);

            return this;
        }
    });

    views.deploymentTypeList = Backbone.View.extend({
        className: 'table',
        tagName: 'table',
        template: _.template(deploymentTypeListTemplate),
        initialize: function() {
            this.model.bind('reset', this.render, this);
        },
        render: function() {
            this.$el.html(this.template({deploymentTypes: this.model}));
            return this;
        }
    });

    return views;
});
