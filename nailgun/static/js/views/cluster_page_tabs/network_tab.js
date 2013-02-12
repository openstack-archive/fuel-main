define(
[
    'models',
    'views/common',
    'views/dialogs',
    'text!templates/cluster/network_tab.html',
    'text!templates/cluster/network_tab_view.html',
    'text!templates/cluster/verify_network_control.html',
    'text!templates/cluster/verify_network_failed.html'
],
function(models, commonViews, dialogViews, networkTabTemplate, networkTabViewModeTemplate, networkTabVerificationControlTemplate, networkTabVerificationFailedTableTemplate) {
    'use strict';
    var NetworkTab, NetworkTabVerificationControl, NetworkTabVerificationFailedTable;

    NetworkTab = commonViews.Tab.extend({
        template: _.template(networkTabTemplate),
        viewModeTemplate: _.template(networkTabViewModeTemplate),
        updateInterval: 3000,
        dataDbState: {},
        hasChanges: false,
        events: {
            'keyup .row input': 'makeChanges',
            'change .row select': 'makeChanges',
            'click .apply-btn:not([disabled])': 'apply',
            'click .verify-networks-btn:not([disabled])': 'verifyNetworks',
            'click .nav a:not(.active)': 'changeMode',
            'click .net-manager input:not([checked])': 'changeManager',
            'keyup .range': 'displayRange'
        },
        checkForChanges: function() {
            this.setValues();
            var noChanges = _.isEqual(this.networks.toJSON(), this.dataDbState.settings) && this.model.get('net_manager') == this.dataDbState.manager;
            this.$('.apply-btn').attr('disabled', noChanges);
            this.hasChanges = !noChanges;
        },
        makeChanges: function(e) {
            var row;
            if (e) {
                row = this.$(e.target).parents('.control-group');
            } else {
                row = this.$('.control-group[data-network-name=fixed]');
            }
            row.removeClass('error').find('.help-inline').text('');
            this.networks.get(row.data('network-id')).on('error', function(model, errors) {
                row.addClass('error').find('.help-inline').text(errors.cidr || errors.vlan_start || errors.amount);
            }, this);
            this.networks.get(row.data('network-id')).set({
                cidr: $('.cidr input', row).val(),
                vlan_start: $('.vlan_start input:first', row).val(),
                amount: this.model.get('net_manager') == 'FlatDHCPManager' ? 1 : $('.amount input', row).val(),
                network_size: parseInt($('.network_size select', row).val(), 10)
            });
            this.checkForChanges();
            this.renderVerificationControl();
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
                this.$('.vlan-end').show();
            } else {
                this.$('.fixed-header .vlan').text('VLAN ID');
                this.$('.vlan-end').hide();
            }
        },
        changeManager: function(e) {
            this.$('.net-manager input').attr('checked', false);
            this.$(e.target).attr('checked', true);
            this.model.set({net_manager: this.$(e.target).val()}, {silent: true});
            this.checkForChanges();
            this.$('.fixed-row .amount, .fixed-header .amount, .fixed-row .network_size, .fixed-header .size').toggle().removeClass('hide');
            this.displayRange();
            this.renderVerificationControl();
        },
        setValues: function() {
            var valid = true;
            this.networks.each(function(network) {
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
                            this.hasChanges = false;
                            this.dataDbState.settings = this.networks.toJSON();
                            this.dataDbState.manager = this.model.get('net_manager');
                        }
                    }, this),
                    complete: _.bind(function() {
                        this.model.fetch();
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
            var task = this.model.task('verify_networks');
            if (task && task.get('status') == 'running' && (force || app.page.$el.find(this.el).length)) {
                task.fetch({complete: _.bind(this.scheduleUpdate, this)});
            } else if (task && task.get('status') == 'error') {
                this.renderVerificationFailedTable();
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
                    this.model.get('tasks')
                        .fetch({data: {cluster_id: this.model.id}})
                        .done(_.bind(this.scheduleUpdate, this));
                }, this)
            });
        },
        verifyNetworks: function() {
            if (this.setValues()) {
                this.$('.verify-networks-btn').attr('disabled', true);
                this.startVerification();
            }
        },
        beforeTearDown: function() {
            if (this.timeout) {
                clearTimeout(this.timeout);
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
            this.model.get('tasks').bind('reset', this.bindTaskEvents, this);
            this.bindTaskEvents();
        },
        initialize: function(options) {
            _.defaults(this, options);
            this.model.bind('change:tasks', this.bindEvents, this);
            this.bindEvents();
            var complete = _.after(2, _.bind(function() {
                this.dataDbState.settings = this.networks.toJSON();
                this.dataDbState.manager = this.model.get('net_manager');
                this.render();
            }, this));
            this.model.fetch().done(complete);
            this.networks = new models.Networks();
            this.networks.deferred = this.networks.fetch({data: {cluster_id: this.model.id}});
            this.networks.deferred.done(complete);
            this.model.set({'networks': this.networks}, {silent: true});
        },
        showVerificationErrors: function() {
            var task = this.model.task('verify_networks', 'error') || this.model.task('check_networks', 'error');
            if (task && task.get('result').length) {
                var verificationResult = task.get('result');
                _.each(verificationResult, function(failedNetwork) {
                    _.each(failedNetwork['errors'], function(field) {
                        this.$('.control-group[data-network-id=' + failedNetwork['id'] + ']').find('.' + field).children().addClass('error');
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
            this.$el.html(this.template({cluster: this.model, networks: this.networks, hasChanges: this.hasChanges}));
            this.renderVerificationControl();
            return this;
        }
    });

    NetworkTabVerificationControl = Backbone.View.extend({
        template: _.template(networkTabVerificationControlTemplate),
        initialize: function(options) {
            _.defaults(this, options);
        },
        removeVerificationTask: function() {
            var task = this.model.task('verify_networks') || this.model.task('check_networks');
            if (task && task.get('status') != 'running') {
                this.model.get('tasks').remove(task);
                task.destroy({silent: true});
            }
        },
        render: function() {
            this.$el.html(this.template({cluster: this.model, networks: this.networks}));
            this.removeVerificationTask();
            return this;
        }
    });

    NetworkTabVerificationFailedTable = Backbone.View.extend({
        template: _.template(networkTabVerificationFailedTableTemplate),
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
