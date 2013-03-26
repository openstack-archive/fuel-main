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
            // validate data per each change
            this.networks.get(row.data('network-id')).set({
                cidr: $('.cidr input', row).val(),
                vlan_start: parseInt($('.vlan_start input:first', row).val(), 10),
                amount: this.manager == 'FlatDHCPManager' || this.networks.get(row.data('network-id')).get('name') != 'fixed' ? 1: parseInt(this.$('input[name=fixed-amount]').val(), 10),
                network_size: parseInt($('.network_size select', row).val(), 10)
            }, {validate: true});
            // check for changes
            var noChanges = _.isEqual(this.model.get('networks').toJSON(), this.networks.toJSON()) && this.model.get('net_manager') == this.manager;
            this.defaultButtonsState(noChanges);
            this.hasChanges = !noChanges;
            app.page.removeVerificationTask();
        },
        changeManager: function(e) {
            this.manager = this.$(e.currentTarget).val();
            this.changeNetworks();
            this.render();
            this.$('input[name=fixed-amount]').val(this.fixedAmount);
        },
        startVerification: function() {
            var task = new models.Task();
            var options = {
                method: 'PUT',
                url: _.result(this.model, 'url') + '/verify/networks',
                data: JSON.stringify(this.networks)
            };
            task.save({}, options)
                .fail(_.bind(function() {
                        var dialog = new dialogViews.SimpleMessage({error: true, title: 'Network verification'});
                        app.page.registerSubView(dialog);
                        dialog.render();
                    }, this))
                .always(_.bind(function() {
                    this.model.get('tasks').fetch({data: {cluster_id: this.model.id}, reset: true}).done(_.bind(this.scheduleUpdate, this));
                }, this));
        },
        verifyNetworks: function() {
            if (!this.$('.control-group.error').length) {
                app.page.removeVerificationTask().done(_.bind(this.startVerification, this));
            }
        },
        applyChanges: function() {
            if (!this.$('.control-group.error').length) {
                this.disableControls();
                this.model.save({net_manager: this.manager}, {patch: true, wait: true});
                var deferred;
                deferred = Backbone.sync('update', this.networks, {url: _.result(this.model, 'url') + '/save/networks'})
                    .always(_.bind(function() {
                        this.model.fetch().done(_.bind(this.render, this));
                    }, this))
                    .done(_.bind(function(task) {
                        if (task && task.status == 'error') {
                            this.defaultButtonsState(false);
                        } else {
                            this.model.set({networks: this.networks.clone()});
                            this.setInitialData();
                        }
                    }, this))
                    .fail(_.bind(function() {
                        this.defaultButtonsState(false);
                        var dialog = new dialogViews.SimpleMessage({error: true, title: 'Networks'});
                        app.page.registerSubView(dialog);
                        dialog.render();
                    }, this));
                return deferred;
            }
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
        bindTaskEvents: function() {
            var task = this.model.task('verify_networks') || this.model.task('check_networks', 'error') || this.model.task('deploy', 'running');
            if (task) {
                task.bind('change:status', this.render, this);
                if (this.networks) {
                    this.render();
                }
            }
        },
        bindEvents: function() {
            this.model.get('tasks').bind('remove', this.renderVerificationControl, this);
            this.model.get('tasks').bind('reset', this.bindTaskEvents, this);
            this.bindTaskEvents();
        },
        setInitialData: function() {
            this.hasChanges = false;
            this.networks = new models.Networks(this.model.get('networks').toJSON());
            this.networks.on('invalid', function(model, errors) {
                this.$('.control-group[data-network-id=' + model.id + ']').addClass('error').find('.help-inline').text(errors.cidr || errors.vlan_start || errors.amount);
            }, this);
            this.manager = this.model.get('net_manager');
            var fixedNetwork = _.find(this.model.get('networks').models, function(network) {return network.get('name') == 'fixed';});
            this.fixedAmount = fixedNetwork.get('amount') || 1;
        },
        revertChanges: function() {
            this.setInitialData();
            app.page.removeVerificationTask().done(_.bind(this.render, this));
        },
        initialize: function(options) {
            _.defaults(this, options);
            this.model.bind('change:tasks', this.bindEvents, this);
            this.bindEvents();
            if (!this.model.get('networks')) {
                this.model.set({networks: new models.Networks()});
                this.model.get('networks').fetch({data: {cluster_id: this.model.id}})
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
            var verificationView = new NetworkTabVerificationControl({model: this.model, networks: this.networks});
            this.registerSubView(verificationView);
            this.$('.verification-control').html(verificationView.render().el);
            this.showVerificationErrors();
        },
        render: function() {
            this.$el.html(this.template({cluster: this.model, networks: this.networks, net_manager: this.manager, hasChanges: this.hasChanges}));
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
            this.$el.html(this.template({cluster: this.model, networks: this.networks}));
            return this;
        }
    });

    return NetworkTab;
});
