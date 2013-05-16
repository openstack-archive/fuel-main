define(
[
    'models',
    'views/common',
    'views/dialogs',
    'text!templates/cluster/network_tab.html',
    'text!templates/cluster/verify_network_control.html'
],
function(models, commonViews, dialogViews, networkTabTemplate, networkTabVerificationControlTemplate) {
    'use strict';
    var NetworkTab, NetworkTabVerificationControl;

    NetworkTab = commonViews.Tab.extend({
        template: _.template(networkTabTemplate),
        updateInterval: 3000,
        hasChanges: false,
        events: {
            'keyup input[type=text]': 'changeNetworks',
            'change select': 'changeNetworks',
            'click .net-manager input:not([checked])': 'changeManager',
            'click .verify-networks-btn:not([disabled])': 'verifyNetworks',
            'click .btn-revert-changes:not([disabled])': 'revertChanges',
            'click .apply-btn:not([disabled])': 'applyChanges'
        },
        defaultButtonsState: function(buttonState) {
            this.$('.btn:not(.verify-networks-btn)').attr('disabled', buttonState);
        },
        disableControls: function() {
            this.$('.btn, input, select').attr('disabled', true);
        },
        changeNetworks: function(e) {
            var row = e ? this.$(e.currentTarget).parents('.control-group') : this.$('.control-group.fixed-network');
            row.removeClass('error').find('.help-inline').text('');
            row.find('.error').removeClass('error');
            if (e) {
                // display vlan ids range
                if (this.$(e.currentTarget).hasClass('range')) {
                    if (parseInt(this.$('input[name=fixed-amount]').val(), 10) > 1 && parseInt(this.$('input[name=fixed-vlan_start]').val(), 10)) {
                        this.$('.fixed-header .vlan').text('VLAN ID range');
                        this.$('input[name=fixed-vlan_start]').addClass('range');
                        var vlanEnd =  parseInt(this.$('input[name=fixed-vlan_start]').val(), 10) + parseInt(this.$('input[name=fixed-amount]').val(), 10) - 1;
                        vlanEnd = vlanEnd > 4094 ? 4094 : vlanEnd;
                        this.$('input[name=fixed-vlan-end]').val(vlanEnd);
                        this.$('.vlan-end').removeClass('hide').show();
                    } else {
                        this.$('.fixed-header .vlan').text('VLAN ID');
                        this.$('.vlan-end').hide();
                    }
                }
                // set fixedAmount
                if (this.$(e.currentTarget).attr('name') == 'fixed-amount' && parseInt(this.$(e.currentTarget).val(), 10)) {
                    this.fixedAmount = parseInt(this.$(e.currentTarget).val(), 10);
                }
            }
            // set floating vlan
            if (e && this.$(e.currentTarget).attr('name') == 'public-vlan_start') {
                var floatingNetwork = this.networkConfiguration.get('networks').findWhere({name: 'floating'});
                this.$('.control-group[data-network-id=' + floatingNetwork.id + ']').removeClass('error').find('.help-inline').text('');
                this.$('input[name=floating-vlan_start]').val(this.$(e.currentTarget).val());
                floatingNetwork.set({
                    vlan_start: parseInt($('input[name=floating-vlan_start]').val(), 10)
                }, {validate: true});
            }
            // validate data per each change
            this.networkConfiguration.get('networks').get(row.data('network-id')).set({
                cidr: $('.cidr input', row).val(),
                vlan_start: Number($('.vlan_start input:first', row).val()),
                amount: this.networkConfiguration.get('net_manager') == 'FlatDHCPManager' || this.networkConfiguration.get('networks').get(row.data('network-id')).get('name') != 'fixed' ? 1: parseInt(this.$('input[name=fixed-amount]').val(), 10),
                network_size: e && this.$(e.currentTarget).parent().hasClass('cidr') && this.$(e.currentTarget).attr('name') != 'fixed-cidr' ? Math.pow(2, 32 - parseInt(_.last($('.cidr input', row).val().split('/')), 10)) : parseInt($('.network_size select', row).val(), 10)
            }, {validate: true});
            // check for changes
            var noChanges = _.isEqual(this.model.get('networkConfiguration').toJSON(), this.networkConfiguration.toJSON()) || _.some(this.networkConfiguration.get('networks').models, 'validationError');
            this.defaultButtonsState(noChanges);
            this.hasChanges = !noChanges;
            this.page.removeVerificationTask();
        },
        changeManager: function(e) {
            this.networkConfiguration.set({net_manager: this.$(e.currentTarget).val()});
            this.$('input[name=fixed-amount]').val(this.fixedAmount);
            this.changeNetworks();
            this.render();
        },
        startVerification: function() {
            var task = new models.Task();
            var options = {
                method: 'PUT',
                url: _.result(this.model, 'url') + '/network_configuration/verify',
                data: JSON.stringify(this.networkConfiguration)
            };
            task.save({}, options)
                .fail(_.bind(function() {
                    var dialog = new dialogViews.SimpleMessage({error: true, title: 'Network verification'});
                    app.page.registerSubView(dialog);
                    dialog.render();
                }, this))
                .always(_.bind(function() {
                    this.model.get('tasks').fetch({data: {cluster_id: this.model.id}}).done(_.bind(this.scheduleUpdate, this));
                }, this));
        },
        verifyNetworks: function() {
            if (!_.some(this.networkConfiguration.get('networks').models, 'validationError')) {
                this.page.removeVerificationTask().done(_.bind(this.startVerification, this));
            }
        },
        applyChanges: function() {
            var deferred;
            if (!_.some(this.networkConfiguration.get('networks').models, 'validationError')) {
                this.disableControls();
                deferred = Backbone.sync('update', this.networkConfiguration, {url: _.result(this.model, 'url') + '/network_configuration'})
                    .always(_.bind(function() {
                        this.model.fetch();
                        this.model.fetchRelated('tasks');
                    }, this))
                    .done(_.bind(function(task) {
                        if (task && task.status == 'error') {
                            this.defaultButtonsState(false);
                        } else {
                            this.hasChanges = false;
                            this.model.get('networkConfiguration').set({
                                net_manager: this.networkConfiguration.get('net_manager'),
                                networks: new models.Networks(this.networkConfiguration.get('networks').toJSON())
                            });
                        }
                    }, this))
                    .fail(_.bind(function() {
                        this.defaultButtonsState(false);
                        var dialog = new dialogViews.SimpleMessage({error: true, title: 'Networks'});
                        app.page.registerSubView(dialog);
                        dialog.render();
                    }, this));
            } else {
                deferred = new $.Deferred();
                deferred.reject();
            }
            return deferred;
        },
        scheduleUpdate: function() {
            if (this.model.task('verify_networks', 'running')) {
                this.registerDeferred($.timeout(this.updateInterval).done(_.bind(this.update, this)));
            }
        },
        update: function() {
            var task = this.model.task('verify_networks', 'running');
            if (task) {
                this.registerDeferred(task.fetch().always(_.bind(this.scheduleUpdate, this)));
            }
        },
        bindTaskEvents: function(task) {
            if (task.get('name') == 'verify_networks' || task.get('name') == 'deploy' || task.get('name') == 'check_networks') {
                return task.on('change:status', this.render, this);
            }
            return null;
        },
        onNewTask: function(task) {
            return this.bindTaskEvents(task) && this.render();
        },
        setInitialData: function() {
            this.hasChanges = false;
            this.networkConfiguration.set({
                net_manager: this.model.get('networkConfiguration').get('net_manager'),
                networks: new models.Networks(this.model.get('networkConfiguration').get('networks').toJSON())
            });
            this.networkConfiguration.get('networks').on('invalid', function(model, errors) {
                this.$('.control-group[data-network-id=' + model.id + ']').addClass('error').find('.help-inline').text(errors.cidr || errors.vlan_start || errors.amount);
            }, this);
            this.fixedAmount = this.networkConfiguration.get('networks').findWhere({name: 'fixed'}).get('amount') || 1;
            _.each(_.filter(this.networkConfiguration.get('networks').models, function(network) {return network.get('name') != 'fixed';}), function(network) {
                var cidr = network.get('cidr');
                network.set({network_size: Math.pow(2, 32 - parseInt(_.last(cidr.split('/')), 10))});
            });
        },
        revertChanges: function() {
            this.setInitialData();
            this.page.removeVerificationTask().done(_.bind(this.render, this));
        },
        initialize: function(options) {
            _.defaults(this, options);
            this.networkConfiguration = new models.NetworkConfiguration();
            this.model.get('tasks').each(this.bindTaskEvents, this);
            this.model.get('tasks').on('add', this.onNewTask, this);
            this.model.get('tasks').on('remove', this.renderVerificationControl, this);
            if (!this.model.get('networkConfiguration')) {
                this.model.set({networkConfiguration: new models.NetworkConfiguration()});
                this.model.get('networkConfiguration').fetch({url: _.result(this.model, 'url') + '/network_configuration'})
                    .done(_.bind(function() {
                        this.setInitialData();
                        this.render();
                    }, this));
            } else {
                this.setInitialData();
            }
        },
        showVerificationErrors: function() {
            var task = this.model.task('verify_networks', 'error') || this.model.task('check_networks', 'error');
            if (task && task.get('result').length) {
                _.each(task.get('result'), function(failedNetwork) {
                    _.each(failedNetwork.errors, function(field) {
                        this.$('.control-group[data-network-id=' + failedNetwork.id + ']').find('.' + field).children().addClass('error');
                    }, this);
                }, this);
            }
        },
        renderVerificationControl: function() {
            var verificationView = new NetworkTabVerificationControl({
                cluster: this.model,
                networks: this.networkConfiguration.get('networks')
            });
            this.registerSubView(verificationView);
            this.$('.verification-control').html(verificationView.render().el);
            this.showVerificationErrors();
        },
        render: function() {
            this.$el.html(this.template({
                networks: this.networkConfiguration.get('networks'),
                net_manager: this.networkConfiguration.get('net_manager'),
                hasChanges: this.hasChanges,
                task: this.model.task('deploy', 'running') || this.model.task('verify_networks', 'running')
            }));
            this.renderVerificationControl();
            return this;
        }
    });

    NetworkTabVerificationControl = Backbone.View.extend({
        template: _.template(networkTabVerificationControlTemplate),
        initialize: function(options) {
            _.defaults(this, options);
        },
        render: function() {
            this.$el.html(this.template({
                cluster: this.cluster,
                networks: this.networks
            }));
            return this;
        }
    });

    return NetworkTab;
});
