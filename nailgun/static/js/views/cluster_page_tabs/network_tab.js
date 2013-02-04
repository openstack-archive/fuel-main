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
        events: {
            'keyup .row input': 'makeChanges',
            'change .row select': 'makeChanges',
            'click .apply-btn:not([disabled])': 'apply',
            'click .verify-networks-btn:not([disabled])': 'verifyNetworks',
            'click .nav a:not(.active)': 'changeMode',
            'click .net-manager input:not([checked])': 'changeManager',
            'keyup .range': 'displayRange'
        },
        makeChanges: function(e) {
            if (e) {
                this.$(e.target).parents('.control-group').removeClass('error').find('.help-inline').text('');
                var attribute = $.trim(this.$(e.target).parent().attr('class'));
                var network = this.$(e.target).parents('.control-group').data('network-id');
                var newValue = this.$(e.target).val();
                if (attribute != 'cidr') {
                    newValue = parseInt(newValue, 10);
                }
                this.networks.get(network).on('error', function(model, errors) {
                    this.$(e.target).parents('.control-group').find('.error .help-inline').text(errors.cidr || errors.vlan_start || errors.amount);
                    this.$(e.target).parents('.control-group').addClass('error');
                }, this);
                this.networks.get(network).set(attribute, newValue);
            } else {
                this.$('.control-group').removeClass('error').find('.help-inline').text('');
            }
            if (_.isEqual(this.networks.toJSON(), this.settingsSaved) && this.model.get('net_manager') == this.$('.net-manager input[checked]').val()) {
                this.$('.apply-btn').attr('disabled', true);
            } else {
                this.$('.apply-btn').attr('disabled', false);
            }
            this.networks.hasChanges = true;
            app.page.removeVerificationTask();
        },
        calculateVlanEnd: function() {
            if (this.$('.net-manager input[checked]').val() == 'VlanManager') {
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
            if (this.$('.net-manager input[checked]').val() == 'VlanManager' && parseInt(this.$('.fixed-row .amount input').val(), 10) > 1 && parseInt(this.$('.fixed-row .vlan_start input:first').val(), 10)) {
                this.$('.fixed-header .vlan').text('VLAN ID range');
                this.$('.fixed-row .vlan_start input:first').addClass('range');
                this.calculateVlanEnd();
                this.$('.vlan-end').show();
            } else {
                this.$('.fixed-header .vlan').text('VLAN ID');
                this.$('.vlan-end').hide();
            }
        },
        changeManager: function(e) {
            this.$('.net-manager input').attr('checked', false);
            this.$(e.target).attr('checked', true);
            this.makeChanges();
            this.$('.fixed-row .amount, .fixed-header .amount, .fixed-row .network_size, .fixed-header .size').toggle().removeClass('hide');
            this.displayRange();
        },
        setValues: function() {
            var valid = true;
            this.$('.control-group').removeClass('error').find('.help-inline').text('');
            this.networks.each(function(network) {
                var row = this.$('.control-group[data-network-name=' + network.get('name') + ']');
                network.on('error', function(model, errors) {
                    valid = false;
                }, this);
                network.set({
                    cidr: $('.cidr input', row).val(),
                    vlan_start: parseInt($('.vlan_start input:first', row).val(), 10),
                    amount: this.$('.net-manager input[checked]').val() == 'FlatDHCPManager' ? 1 : parseInt($('.amount input', row).val(), 10),
                    network_size: parseInt($('.network_size select', row).val(), 10)
                });
            }, this);
            return valid;
        },
        changeMode: function(e) {
            e.preventDefault();
        },
        apply: function() {
            if (this.setValues()) {
                this.$('.apply-btn').attr('disabled', true);
                this.model.update({net_manager: this.$('.net-manager input[checked]').val()});
                Backbone.sync('update', this.networks, {
                    url: '/api/clusters/' + this.model.id + '/save/networks',
                    error: _.bind(function() {
                        this.$('.apply-btn').attr('disabled', false);
                        var dialog = new dialogViews.SimpleMessage({error: true, title: 'Networks'});
                        this.registerSubView(dialog);
                        dialog.render();
                    }, this),
                    success: _.bind(function(task) {
                        if (task && task.status == 'error') {
                            this.$('.apply-btn').attr('disabled', false);
                        } else {
                            this.networks.hasChanges = false;
                            this.settingsSaved = this.networks.toJSON();
                        }
                    }, this),
                    complete: _.bind(function() {
                        this.model.get('tasks').fetch({data: {cluster_id: this.model.id}});
                    }, this)
                });
            }
        },
        scheduleUpdate: function() {
            if (this.model.task('verify_networks', 'running')) {
                this.timeout = _.delay(_.bind(this.update, this), this.updateInterval);
            }
        },
        update: function(force) {
            var task = this.model.task('verify_networks', 'running');
            if (task && (force || app.page.$el.find(this.el).length)) {
                task.fetch({complete: _.bind(this.scheduleUpdate, this)});
            }
        },
        startVerification: function() {
            var task = new models.Task();
            task.save({}, {
                type: 'PUT',
                url: '/api/clusters/' + this.model.id + '/verify/networks',
                data: JSON.stringify(this.networks),
                error:  _.bind(function() {
                        this.$('.verify-networks-btn').attr('disabled', false);
                        var dialog = new dialogViews.SimpleMessage({error: true, title: 'Network verification'});
                        this.registerSubView(dialog);
                        dialog.render();
                    }, this),
                complete: _.bind(function() {
                    this.model.get('tasks').fetch({data: {cluster_id: this.model.id}});
                }, this)
            });
        },
        verifyNetworks: function() {
            if (this.setValues()) {
                this.$('.verify-networks-btn').attr('disabled', true);
                app.page.removeVerificationTask().done(_.bind(this.startVerification, this));
            }
        },
        beforeTearDown: function() {
            if (this.timeout) {
                clearTimeout(this.timeout);
            }
        },
        bindEvents: function() {
            this.model.get('tasks').bind('remove', this.renderVerificationControl, this);
            this.model.get('tasks').bind('reset', function(){
                this.render();
                this.update(true);
            }, this);
            this.model.get('tasks').bind('change:status', function(task) {
                if ((task.get('name') == 'deploy' || task.get('name') == 'verify_networks') && task.get('status') != 'running') {
                    this.render();
                }
            }, this);
        },
        initialize: function(options) {
            _.defaults(this, options);
            this.model.bind('change:tasks', this.bindEvents, this);
            this.bindEvents();
            if (!this.model.get('networks')) {
                this.networks = new models.Networks();
                this.networks.deferred = this.networks.fetch({data: {cluster_id: this.model.id}});
                this.networks.deferred.done(_.bind(this.render, this));
                this.model.set({'networks': this.networks}, {silent: true});
            } else {
                this.networks = this.model.get('networks');
            }
        },
        renderVerificationControl: function() {
            var verificationView = new NetworkTabVerificationControl({model: this.model, networks: this.networks});
            this.registerSubView(verificationView);
            this.$('.verification-control').html(verificationView.render().el);
        },
        render: function() {
            this.settingsSaved = this.networks.toJSON();
            this.$el.html(this.template({cluster: this.model, networks: this.networks}));
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
