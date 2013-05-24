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

                    this.model.get('networkConfiguration').get('networks').each(function(network) {
                        network.set({
                            ip_ranges: [['172.56.2.35', '172.56.2.57']],
                            mask: '255.67.0.1',
                            gateway: '102.87.78.9'
                        });
                    });

            this.networkConfiguration.set({
                net_manager: this.model.get('networkConfiguration').get('net_manager'),
                networks: new models.Networks(this.model.get('networkConfiguration').get('networks').toJSON())
            });
            this.fixedAmount = this.networkConfiguration.get('networks').findWhere({name: 'fixed'}).get('amount') || 1;
            _.each(_.filter(this.networkConfiguration.get('networks').models, function(network) {return network.get('name') != 'fixed';}), function(network) {
                network.set({network_size: utils.calculateNetworkSize(network.get('cidr'))});
            });
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
                    var networkView = new Network({
                        tab: this,
                        networkId: network.id,
                        task: this.task
                    });
                    this.registerSubView(networkView);
                    this.$('.networks-table').append(networkView.render().el);
                }, this);
            }
        },
        render: function() {
            this.task = this.model.task('deploy', 'running') || this.model.task('verify_networks', 'running');
            this.$el.html(this.template({
                net_manager: this.networkConfiguration.get('net_manager'),
                hasChanges: this.hasChanges,
                task: this.task
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
            'click .range-name': 'setIPRangeFocus',
            'click .ip-ranges-add': 'addIPRange',
            'click .ip-ranges-delete': 'deleteIPRange'
        },
        changeNetwork: function(e) {
            var target = this.$(e.currentTarget);
            target.removeClass('error');
            var block = target.parents('div[data-network-id]');
            block.find('.help-inline').text('');
            if (target.attr('name') == 'fixed-amount') {
                this.tab.fixedAmount = parseInt(target.val(), 10) || this.tab.fixedAmount;
            } else if (target.attr('name') == 'public-vlan_start') {
                this.tab.$('div.floating').find('input.error').removeClass('error');
                this.tab.$('div.floating').find('.help-inline').text('');
                this.tab.$('input[name=floating-vlan_start]').val(target.val());
                this.tab.networkConfiguration.get('networks').findWhere({name: 'floating'}).set({vlan_start: parseInt(target.val(), 10)});
            }
            if (target.hasClass('range')) {
                var amount = parseInt(this.$('input[name=fixed-amount]').val(), 10) || 1;
                var vlanEnd = (parseInt(this.$('input[name=fixed-vlan_range-start]').val(), 10) + amount - 1) || 1;
                vlanEnd = vlanEnd > 4094 ? 4094 : vlanEnd;
                this.$('input[name=fixed-vlan_range-end]').val(vlanEnd);
            }
            var ip_ranges = [];
            block.find('.range-row').each(function(index, rangeRow) {
                ip_ranges.push([$(rangeRow).find('input:first').val(), $(rangeRow).find('input:last').val()]);
            });
            this.network.set({
                ip_ranges: ip_ranges,
                cidr: $('.cidr input', block).val(),
                vlan_start: Number($('.vlan_start input', block).val()),
                mask: $('.mask input', block).val(),
                gateway: $('.gateway input', block).val(),
                amount: this.manager == 'FlatDHCPManager' || block.attr('class') != 'fixed' ? 1: parseInt(this.$('input[name=fixed-amount]').val(), 10),
                network_size: target.parent().hasClass('cidr') && target.attr('name') != 'fixed-cidr' ? utils.calculateNetworkSize($('.cidr input', block).val()) : parseInt($('.network_size select', block).val(), 10)
            }, {validate: true});
            this.tab.checkForChanges();
            this.tab.page.removeVerificationTask();
        },
        setIPRangeFocus: function(e) {
            this.$(e.currentTarget).next().find('input:first').focus();
        },
        editIPRange: function(e, add) {
            var row = this.$(e.currentTarget).parents('.range-row');
            var index = this.$('.range-row').index(row);
            if (add) {
                this.network.get('ip_ranges').splice(index + 1, 0, ['', '']);
                var newRow = row.clone();
                newRow.find('input').val('');
                row.after(newRow);
                row.parent().find('.ip-ranges-control').removeClass('hide');
            } else {
                this.network.get('ip_ranges').splice(index , 1);
                row.parent().find('.ip-ranges-delete').parent().toggleClass('hide', row.siblings('.range-row').length == 1);
                row.remove();
            }
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
            this.network = this.tab.networkConfiguration.get('networks').get(this.networkId);
            this.manager = this.tab.networkConfiguration.get('net_manager');
            this.network.on('invalid', function(model, errors) {
                _.each(_.without(_.keys(errors), 'ip_ranges'), _.bind(function(field) {
                    this.$('.' + field).children().addClass('error');
                    this.$('.' + field).siblings('.error').find('.help-inline').text(errors[field]);
                }, this));
                if (errors.ip_ranges) {
                    _.each(errors.ip_ranges, _.bind(function(range) {
                        var row = this.$('.range-row:eq(' + range.index + ')');
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
                net_manager: this.manager,
                task: this.task
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
