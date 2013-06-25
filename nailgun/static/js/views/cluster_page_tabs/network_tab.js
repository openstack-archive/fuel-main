define(
[
    'utils',
    'models',
    'views/common',
    'views/dialogs',
    'text!templates/cluster/network_tab.html',
    'text!templates/cluster/network.html',
    'text!templates/cluster/verify_network_control.html'
],
function(utils, models, commonViews, dialogViews, networkTabTemplate, networkTemplate, networkTabVerificationControlTemplate) {
    'use strict';
    var NetworkTab, Network, NetworkTabVerificationControl;

    NetworkTab = commonViews.Tab.extend({
        template: _.template(networkTabTemplate),
        updateInterval: 3000,
        hasChanges: false,
        events: {
            'click .net-manager input:not([checked])': 'changeManager',
            'click .verify-networks-btn:not([disabled])': 'verifyNetworks',
            'click .btn-revert-changes:not([disabled])': 'revertChanges',
            'click .apply-btn:not([disabled])': 'applyChanges'
        },
        defaultButtonsState: function(validationErrors) {
            this.$('.btn:not(.ip-ranges)').attr('disabled', !this.hasChanges || validationErrors);
            this.$('.btn.verify-networks-btn').attr('disabled', validationErrors);
        },
        disableControls: function() {
            this.$('.btn, input, select').attr('disabled', true);
        },
        isLocked: function() {
            return this.model.get('status') != 'new' || !!this.model.task('deploy', 'running') || !!this.model.task('verify_networks', 'running');
        },
        isVerificationLocked: function() {
            return !!this.model.task('deploy', 'running') || !!this.model.task('verify_networks', 'running');
        },
        checkForChanges: function() {
            var noChanges = _.isEqual(this.model.get('networkConfiguration').toJSON(), this.networkConfiguration.toJSON());
            this.hasChanges = !noChanges;
            this.defaultButtonsState(_.some(this.networkConfiguration.get('networks').models, 'validationError'));
        },
        changeManager: function(e) {
            this.$('.net-manager input').attr('checked', function(el, oldAttr) {return !oldAttr;});
            this.networkConfiguration.set({net_manager: this.$(e.currentTarget).val()});
            this.networkConfiguration.get('networks').findWhere({name: 'fixed'}).set({amount: this.$(e.currentTarget).val() == 'VlanManager' ? this.fixedAmount : 1});
            this.renderNetworks();
            this.checkForChanges();
            this.page.removeVerificationTask();
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
                    utils.showErrorDialog({title: 'Network verification'});
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
        revertChanges: function() {
            this.setInitialData();
            this.page.removeVerificationTask().done(_.bind(this.render, this));
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
                        utils.showErrorDialog({title: 'Networks'});
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
            this.fixedAmount = this.networkConfiguration.get('networks').findWhere({name: 'fixed'}).get('amount') || 1;
            _.each(this.networkConfiguration.get('networks').filter(function(network) {return network.get('name') != 'fixed';}), function(network) {
                network.set({network_size: utils.calculateNetworkSize(network.get('cidr'))});
            });
        },
        initialize: function(options) {
            _.defaults(this, options);
            this.networkConfiguration = new models.NetworkConfiguration();
            this.model.on('change:status', this.render, this);
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
                        this.$('div[data-network-id=' + failedNetwork.id + ']').find('.' + field).children().addClass('error');
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
        renderNetworks: function() {
            if (this.networkConfiguration.get('networks')) {
                this.tearDownRegisteredSubViews();
                this.$('.networks-table').html('');
                this.networkConfiguration.get('networks').each(function(network) {
                    var networkView = new Network({network: network, tab: this});
                    this.registerSubView(networkView);
                    this.$('.networks-table').append(networkView.render().el);
                }, this);
            }
        },
        render: function() {
            this.$el.html(this.template({
                net_manager: this.networkConfiguration.get('net_manager'),
                hasChanges: this.hasChanges,
                locked: this.isLocked(),
                verificationLocked: this.isVerificationLocked()
            }));
            this.renderNetworks();
            this.renderVerificationControl();
            return this;
        }
    });

    Network = Backbone.View.extend({
        template: _.template(networkTemplate),
        events: {
            'keyup input[type=text]': 'changeNetwork',
            'change select': 'changeNetwork',
            'change .use-vlan-tagging': 'changeNetwork',
            'click .range-name': 'setIPRangeFocus',
            'click .ip-ranges-add': 'addIPRange',
            'click .ip-ranges-delete': 'deleteIPRange'
        },
        changeNetwork: function(e) {
            var target = $(e.currentTarget);
            target.removeClass('error');
            this.$('.help-inline').text('');
            if (target.attr('name') == 'fixed-amount') {
                this.tab.fixedAmount = parseInt(target.val(), 10) || this.tab.fixedAmount;
            } else if (target.attr('name') == 'public-vlan_start') {
                this.tab.$('div.floating').find('input.error').removeClass('error');
                this.tab.$('div.floating').find('.help-inline').text('');
                this.tab.$('input[name=floating-vlan_start]').val(target.val());
                this.tab.networkConfiguration.get('networks').findWhere({name: 'floating'}).set({vlan_start: parseInt(target.val(), 10)});
            } else if (target.hasClass('use-vlan-tagging')) {
                target.parents('.network-attribute').find('input[type=text]').toggle(target.is(':checked'));
            }
            if (target.hasClass('range')) {
                var amount = parseInt(this.$('input[name=fixed-amount]').val(), 10) || 1;
                var vlanEnd = (parseInt(this.$('input[name=fixed-vlan_range-start]').val(), 10) + amount - 1) || 1;
                vlanEnd = vlanEnd > 4094 ? 4094 : vlanEnd;
                this.$('input[name=fixed-vlan_range-end]').val(vlanEnd);
            }
            this.updateNetworkFromForm();
            this.tab.checkForChanges();
            this.tab.page.removeVerificationTask();
        },
        updateNetworkFromForm: function() {
            var ip_ranges = [];
            this.$('.ip-range-row').each(function(index, rangeRow) {
                var range = [$(rangeRow).find('input:first').val(), $(rangeRow).find('input:last').val()];
                if (!_.isEqual(range, ['', ''])) {
                    ip_ranges.push(range);
                }
            });
            var fixedNetworkOnVlanManager = this.tab.networkConfiguration.get('net_manager') == 'VlanManager' && this.network.get('name') == 'fixed';
            this.network.set({
                ip_ranges: ip_ranges,
                cidr: this.$('.cidr input').val(),
                vlan_start: fixedNetworkOnVlanManager || this.$('.use-vlan-tagging:checked').length ? Number(this.$('.vlan_start input').val()) : null,
                netmask: this.$('.netmask input').val(),
                gateway: this.$('.gateway input').val(),
                amount: fixedNetworkOnVlanManager ? parseInt(this.$('input[name=fixed-amount]').val(), 10) : 1,
                network_size: fixedNetworkOnVlanManager ? parseInt(this.$('.network_size select').val(), 10) : utils.calculateNetworkSize(this.$('.cidr input').val())
            }, {validate: true});
        },
        setIPRangeFocus: function(e) {
            this.$(e.currentTarget).next().find('input:first').focus();
        },
        editIPRange: function(e, add) {
            if (this.tab.isLocked()) {
                return;
            }
            var row = this.$(e.currentTarget).parents('.ip-range-row');
            if (add) {
                var newRow = row.clone();
                newRow.find('input').removeClass('error').val('');
                newRow.find('.help-inline').text('');
                row.after(newRow);
                row.parent().find('.ip-ranges-control').removeClass('hide');
            } else {
                row.parent().find('.ip-ranges-delete').parent().toggleClass('hide', row.siblings('.ip-range-row').length == 1);
                row.remove();
            }
            this.updateNetworkFromForm();
            this.tab.checkForChanges();
            this.tab.page.removeVerificationTask();
        },
        addIPRange: function(e) {
            this.editIPRange(e, true);
        },
        deleteIPRange: function(e) {
            this.editIPRange(e, false);
        },
        initialize: function(options) {
            _.defaults(this, options);
            this.network.on('invalid', function(model, errors) {
                _.each(_.without(_.keys(errors), 'ip_ranges'), _.bind(function(field) {
                    this.$('.' + field).children().addClass('error');
                    this.$('.' + field).parents('.network-attribute').find('.error .help-inline').text(errors[field]);
                }, this));
                if (errors.ip_ranges) {
                    _.each(errors.ip_ranges, _.bind(function(range) {
                        var row = this.$('.ip-range-row:eq(' + range.index + ')');
                        row.find('input:first').toggleClass('error', !!range.start);
                        row.find('input:last').toggleClass('error', !!range.end);
                        row.find('.help-inline').text(range.start || range.end);
                    }, this));
                }
            }, this);
        },
        render: function() {
            this.$el.html(this.template({
                publicVlan: this.tab.networkConfiguration.get('networks').findWhere({name: 'public'}).get('vlan_start'),
                network: this.network,
                net_manager: this.tab.networkConfiguration.get('net_manager'),
                locked: this.tab.isLocked()
            }));
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
