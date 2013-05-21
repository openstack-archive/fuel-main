define(
[
    'utils',
    'models',
    'views/common',
    'views/dialogs',
    'text!templates/cluster/network_tab.html',
    'text!templates/cluster/verify_network_control.html'
],
function(utils, models, commonViews, dialogViews, networkTabTemplate, networkTabVerificationControlTemplate) {
    'use strict';
    var NetworkTab, NetworkTabVerificationControl;

    NetworkTab = commonViews.Tab.extend({
        template: _.template(networkTabTemplate),
        updateInterval: 3000,
        hasChanges: false,
        events: {
            'keyup input[type=text]': 'changeNetworks',
            'change select': 'changeNetworks',
            'click .range-name': 'setIPRangeFocus',
            'click .net-manager input:not([checked])': 'changeManager',
            'click .ip-ranges-add': 'addIPRange',
            'click .ip-ranges-delete': 'deleteIPRange',
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
            var target = e ? this.$(e.currentTarget) : {};
            var block = e ? target.parents('div[data-network-id]') : this.$('div.fixed');
            block.find('.help-inline').text('');
            var ip_ranges = [];
            if (e) {
                target.removeClass('error');
                // vlan ids range
                if (target.hasClass('range')) {
                    var vlanEnd =  parseInt(this.$('input[name=fixed-vlan_range-start]').val(), 10) + parseInt(this.$('input[name=fixed-amount]').val(), 10) - 1;
                    vlanEnd = vlanEnd > 4094 ? 4094 : vlanEnd;
                    this.$('input[name=fixed-vlan_range-end]').val(vlanEnd);
                }
                // set fixedAmount
                if (target.attr('name') == 'fixed-amount') {
                    this.fixedAmount = parseInt(target.val(), 10) || this.fixedAmount;
                // set floating vlan
                } else if (target.attr('name') == 'public-vlan_start') {
                    this.$('div.floating').find('.error').removeClass('error');
                    this.$('div.floating').find('.help-inline').text('');
                    this.$('input[name=floating-vlan_start]').val(target.val());
                    this.networkConfiguration.get('networks').findWhere({name: 'floating'}).set({
                        vlan_start: parseInt(target.val(), 10)
                    }, {validate: true});
                }
                block.find('.range-row').each(function(rangeRow) {
                    ip_ranges.push([rangeRow.find('input:first').val(), rangeRow.find('input:last').val()]);
                });
            }
            // validate data per each change
            this.networkConfiguration.get('networks').get(block.data('network-id')).set({
                ip_ranges: ip_ranges,
                cidr: $('.cidr input', block).val(),
                vlan_start: Number($('.vlan_range input:first', block).val()),
                netmask: $('.netmask input', block).val(),
                gateway: $('.gateway input', block).val(),
                amount: this.networkConfiguration.get('net_manager') == 'FlatDHCPManager' || block.attr('class') != 'fixed' ? 1: parseInt(this.$('input[name=fixed-amount]').val(), 10),
                network_size: e && target.parent().hasClass('cidr') && target.attr('name') != 'fixed-cidr' ? Math.pow(2, 32 - parseInt(_.last($('.cidr input', block).val().split('/')), 10)) : parseInt($('.network_size select', block).val(), 10)
            }, {validate: true});
            // check for changes
            var noChanges = _.isEqual(this.model.get('networkConfiguration').toJSON(), this.networkConfiguration.toJSON()) || _.some(this.networkConfiguration.get('networks').models, 'validationError');
            this.defaultButtonsState(noChanges);
            this.hasChanges = !noChanges;
            this.page.removeVerificationTask();
        },
        setIPRangeFocus: function(e) {
            this.$(e.currentTarget).next().find('input:first').focus();
        },
        changeManager: function(e) {
            this.networkConfiguration.set({net_manager: this.$(e.currentTarget).val()});
            this.$('input[name=fixed-amount]').val(this.fixedAmount);
            this.changeNetworks();
            this.render();
        },
        editIPRange: function(e, add) {
            var network = this.$(e.currentTarget).parents('div[data-network-id]').data('network-id');
            var ip_ranges = this.networkConfiguration.get('networks').get(network).get('ip_ranges');
            var updatedRanges;
            if (add) {
                updatedRanges = _.union(ip_ranges, ['', '']);
            } else {
                var rangeIndex = this.$('.range-row').index(this.$(e.currentTarget).parents('.range-row'));
                updatedRanges = _.filter(ip_ranges, function(range, index) {return index != rangeIndex;});
            }
            this.networkConfiguration.get('networks').get(network).set({ip_ranges: updatedRanges});
            this.render();
        },
        addIPRange: function(e) {
            this.editIPRange(e, true);
        },
        deleteIPRange: function(e) {
            this.editIPRange(e, false);
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
            this.networkConfiguration.get('networks').on('invalid', function(model, errors) {
                _.each(_.without(_.keys(errors), 'ip_ranges'), _.bind(function(field) {
                    this.$('div[data-network-id=' + model.id + ']').find('.' + field).children().addClass('error');
                    this.$('div[data-network-id=' + model.id + ']').find('.help-inline').text(errors[field]);
                }, this));
                if (errors.ip_ranges.length) {
                    _.each(errors.ip_ranges, _.bind(function(range) {
                        var row = this.$('div[data-network-id=' + model.id + ']').find('.range-row:eq(' + range.index + ')');
                        row.find('input:first').addClass('error', range.start);
                        row.find('input:last').addClass('error', range.end);
                        row.find('.help-inline').text(range.start || range.end);
                    }, this));
                }
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
        render: function() {
                if (this.networkConfiguration && this.networkConfiguration.get('networks')) {
                    _.each(this.networkConfiguration.get('networks').models, function(network) {
                        network.set({ip_ranges: [['172.56.02.03', '172.56.02.45'], ['', '']]});
                    });
                }

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
