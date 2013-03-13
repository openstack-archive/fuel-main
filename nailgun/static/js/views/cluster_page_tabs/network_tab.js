define(
[
    'models',
    'views/common',
    'views/dialogs',
    'text!templates/cluster/network_tab.html',
    'text!templates/cluster/network_tab_view.html',
    'text!templates/cluster/verify_network_control.html'
],
function(models, commonViews, dialogViews, networkTabTemplate, networkTabViewModeTemplate, networkTabVerificationControlTemplate) {
    'use strict';
    var NetworkTab, NetworkTabVerificationControl;

    NetworkTab = commonViews.Tab.extend({
        template: _.template(networkTabTemplate),
        viewModeTemplate: _.template(networkTabViewModeTemplate),
        updateInterval: 3000,
        hasChanges: false,
        events: {
            'keyup .row input': 'makeChanges',
            'change .row select': 'makeChanges',
            'click .apply-btn:not([disabled])': 'applyChanges',
            'click .verify-networks-btn:not([disabled])': 'verifyNetworks',
            'click .btn-revert-changes:not([disabled])': 'revertChanges',
            'click .net-manager input:not([checked])': 'changeManager',
            'keyup .range': 'displayRange'
        },
        defaultButtonsState: function(buttonState) {
            this.$('.btn:not(.verify-networks-btn)').attr('disabled', buttonState);
        },
        disableControls: function() {
            this.$('.btn, input, select').attr('disabled', true);
        },
        checkForChanges: function() {
            this.setValues();
            var noChanges = _.isEqual(this.model.get('networks').toJSON(), this.model.get('networksDbState').settings) && this.model.get('net_manager') == this.model.get('networksDbState').manager;
            this.defaultButtonsState(noChanges);
            this.hasChanges = !noChanges;
        },
        makeChanges: function(e) {
            var row = e ? this.$(e.target).parents('.control-group') : this.$('.control-group[data-network-name=fixed]');
            this.$('.control-group .error').removeClass('error');
            row.removeClass('error').find('.help-inline').text('');
            this.model.get('networks').get(row.data('network-id')).on('error', function(model, errors) {
                row.addClass('error').find('.help-inline').text(errors.cidr || errors.vlan_start || errors.amount);
            }, this);
            this.model.get('networks').get(row.data('network-id')).set({
                cidr: $('.cidr input', row).val(),
                vlan_start: $('.vlan_start input:first', row).val(),
                amount: this.model.get('net_manager') == 'FlatDHCPManager' ? 1 : $('.amount input', row).val(),
                network_size: parseInt($('.network_size select', row).val(), 10)
            });
            this.checkForChanges();
            app.page.removeVerificationTask();
        },
        calculateVlanEnd: function() {
            if (this.model.get('net_manager') == 'VlanManager') {
                var amount = parseInt(this.$('.fixed-row .amount input').val(), 10);
                var vlanStart = parseInt(this.$('.fixed-row .vlan_start input:first').val(), 10);
                var vlanEnd =  vlanStart + amount - 1;
                if (vlanEnd > 4094) {
                    vlanEnd = 4094;
                }
                this.$('input.vlan-end').val(vlanEnd);
            }
        },
        displayRange: function() {
            if (this.model.get('net_manager') == 'VlanManager' && parseInt(this.$('.fixed-row .amount input').val(), 10) > 1 && parseInt(this.$('.fixed-row .vlan_start input:first').val(), 10)) {
                this.$('.fixed-header .vlan').text('VLAN ID range');
                this.$('.fixed-row .vlan_start input:first').addClass('range');
                this.calculateVlanEnd();
                this.$('.vlan-end').removeClass('hide').show();
            } else {
                this.$('.fixed-header .vlan').text('VLAN ID');
                this.$('.vlan-end').hide();
            }
        },
        changeManager: function(e) {
            this.$('.net-manager input').attr('checked', false);
            this.$(e.target).attr('checked', true);
            this.model.set({net_manager: this.$(e.target).val()}, {silent: true});
            this.$('.control-group .error').removeClass('error');
            this.checkForChanges();
            this.$('.fixed-row .amount, .fixed-header .amount, .fixed-row .network_size, .fixed-header .size').toggle().removeClass('hide');
            this.displayRange();
            app.page.removeVerificationTask();
        },
        setValues: function() {
            var valid = true;
            this.model.get('networks').each(function(network) {
                var row = this.$('.control-group[data-network-name=' + network.get('name') + ']');
                network.on('error', function(model, errors) {
                    valid = false;
                }, this);
                network.set({
                    cidr: $('.cidr input', row).val(),
                    vlan_start: parseInt($('.vlan_start input:first', row).val(), 10),
                    amount: this.model.get('net_manager') == 'FlatDHCPManager' ? 1 : parseInt($('.amount input', row).val(), 10),
                    network_size: parseInt($('.network_size select', row).val(), 10)
                });
            }, this);
            return valid;
        },
        applyChanges: function() {
            if (this.setValues()) {
                this.disableControls();
                this.model.update({net_manager: this.$('.net-manager input[checked]').val()});
                Backbone.sync('update', this.model.get('networks'), {
                    url: '/api/clusters/' + this.model.id + '/save/networks',
                    error: _.bind(function() {
                        this.defaultButtonsState(false);
                        var dialog = new dialogViews.SimpleMessage({error: true, title: 'Networks'});
                        this.registerSubView(dialog);
                        dialog.render();
                    }, this),
                    success: _.bind(function(task) {
                        if (task && task.status == 'error') {
                            this.defaultButtonsState(false);
                        } else {
                            this.hasChanges = false;
                            this.model.get('networksDbState').settings = this.model.get('networks').toJSON();
                            this.model.get('networksDbState').manager = this.model.get('net_manager');
                        }
                    }, this),
                    complete: _.bind(function() {
                        this.render();
                        this.model.fetch();
                    }, this)
                });
            }
        },
        scheduleUpdate: function() {
            if (this.model.task('verify_networks', 'running')) {
                this.registerDeferred($.timeout(this.updateInterval).done(_.bind(this.update, this)));
            }
        },
        update: function(force) {
            var task = this.model.task('verify_networks', 'running');
            if (task && (force || app.page.$el.find(this.el).length)) {
                this.registerDeferred(task.fetch({complete: _.bind(this.scheduleUpdate, this)}));
            }
        },
        startVerification: function() {
            var task = new models.Task();
            task.save({}, {
                type: 'PUT',
                url: '/api/clusters/' + this.model.id + '/verify/networks',
                data: JSON.stringify(this.model.get('networks')),
                error:  _.bind(function() {
                        this.$('.verify-networks-btn').attr('disabled', false);
                        var dialog = new dialogViews.SimpleMessage({error: true, title: 'Network verification'});
                        this.registerSubView(dialog);
                        dialog.render();
                    }, this),
                complete: _.bind(function() {
                    var request = this.model.get('tasks').fetch({data: {cluster_id: this.model.id}});
                    request.done(_.bind(this.scheduleUpdate, this));
                    this.registerDeferred(request);
                }, this)
            });
        },
        verifyNetworks: function() {
            if (this.setValues()) {
                this.$('.verify-networks-btn').attr('disabled', true);
                app.page.removeVerificationTask().done(_.bind(this.startVerification, this));
            }
        },
        bindTaskEvents: function() {
            var task = this.model.task('verify_networks') || this.model.task('check_networks', 'error') || this.model.task('deploy', 'running');
            if (task) {
                task.bind('change:status', this.render, this);
                if (this.model.get('networks')) {
                    this.render();
                }
            }
        },
        bindEvents: function() {
            this.model.get('tasks').bind('remove', this.renderVerificationControl, this);
            this.model.get('tasks').bind('reset', this.bindTaskEvents, this);
            this.bindTaskEvents();
        },
        revertChanges: function() {
            this.hasChanges = false;
            this.model.set({
                net_manager: this.model.get('networksDbState').manager,
                networks: new models.Networks(this.model.get('networksDbState').settings)
            }, {silent: true});
            this.model.get('networks').deferred = new $.Deferred();
            this.model.get('networks').deferred.resolve();
            app.page.removeVerificationTask().done(_.bind(this.render, this));
        },
        initialize: function(options) {
            _.defaults(this, options);
            this.model.bind('change:tasks', this.bindEvents, this);
            this.bindEvents();
            if (!this.model.get('networks')) {
                this.model.set({'networks': new models.Networks()}, {silent: true});
                this.model.get('networks').deferred = this.model.get('networks').fetch({data: {cluster_id: this.model.id}});
                this.model.get('networks').deferred.done(_.bind(function() {
                    var networksDbState = {
                        settings: this.model.get('networks').toJSON(),
                        manager: this.model.get('net_manager')
                    };
                    this.model.set({'networksDbState': networksDbState}, {silent: true});
                    this.render();
                }, this));
            } else {
                this.revertChanges();
            }
        },
        showVerificationErrors: function() {
            var task = this.model.task('verify_networks', 'error') || this.model.task('check_networks', 'error');
            if (task && task.get('result').length) {
                var verificationResult = task.get('result');
                _.each(verificationResult, function(failedNetwork) {
                    _.each(failedNetwork.errors, function(field) {
                        this.$('.control-group[data-network-id=' + failedNetwork.id + ']').find('.' + field).children().addClass('error');
                    }, this);
                }, this);
            }
        },
        renderVerificationControl: function() {
            var verificationView = new NetworkTabVerificationControl({model: this.model, networks: this.model.get('networks')});
            this.registerSubView(verificationView);
            this.$('.verification-control').html(verificationView.render().el);
            this.showVerificationErrors();
        },
        render: function() {
            this.$el.html(this.template({cluster: this.model, networks: this.model.get('networks'), hasChanges: this.hasChanges}));
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
