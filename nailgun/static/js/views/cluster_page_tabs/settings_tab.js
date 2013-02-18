define(
[
    'models',
    'views/common',
    'text!templates/cluster/settings_tab.html',
    'text!templates/cluster/settings_group.html'
],
function(models, commonViews, settingsTabTemplate, settingsGroupTemplate) {
    'use strict';
    var SettingsTab, SettingsGroup;

    SettingsTab = commonViews.Tab.extend({
        template: _.template(settingsTabTemplate),
        hasChanges: false,
        events: {
            'click .btn-apply-changes:not([disabled])': 'applyChanges',
            'click .btn-revert-changes:not([disabled])': 'revertChanges',
            'click .btn-load-defaults:not([disabled])': 'loadDefaults'
        },
        defaultButtonsState: function(buttonState) {
            this.$('.btn').attr('disabled', buttonState);
            this.$('.btn-load-defaults').attr('disabled', !buttonState);
        },
        disableControls: function() {
            this.$('.btn, input').attr('disabled', true);
        },
        collectData: function() {
            var data = {};
            _.each(this.$('legend.openstack-settings'), function(legend) {
                var param = $(legend).text();
                data[param] = {};
                _.each($(legend).next().find('.setting'), function(settingDom) {
                    var setting = $(settingDom).data('setting');
                    data[param][setting] = {};
                    if ($(settingDom).hasClass('openstack-sub-title')) {
                        data[param][setting].label = $(settingDom).text();
                        data[param][setting].value = $(settingDom).next().find('input[type=radio]:checked').val();
                        data[param][setting].values = [];
                        _.each($(settingDom).next().find('input[type=radio]'), function(input) {
                            var option = {};
                            option.data = $(input).val();
                            option.display_name = $(input).parents('.parameter-control').siblings('.parameter-name').text();
                            option.description = $(input).parents('.parameter-box').next('.description').text();
                            data[param][setting].values.push(option);
                        });
                    } else {
                        data[param][setting].label = $(settingDom).find('.openstack-sub-title').text();
                        data[param][setting].description = $(settingDom).find('.description').text() || $(settingDom).next('.description').text();
                        data[param][setting].value = $(settingDom).find('input[type=text]').val();
                        if (!data[param][setting].value) {
                            data[param][setting].value = $(settingDom).find('input[type=checkbox]:checked').length ? true : false;
                        }
                    }
                });
            });
            return data;
        },
        checkForChanges: function() {
            var equal = true, data = this.collectData();
            var previousSettings = this.model.get('settings').get('editable');
            _.each(_.keys(previousSettings), function(settings) {
                _.each(_.keys(previousSettings[settings]), function(setting) {
                    if (previousSettings[settings][setting].value != data[settings][setting].value) {
                        equal = false;
                    }
                });
            });
            if (equal) {
                this.defaultButtonsState(true);
                this.hasChanges = false;
            } else {
                this.$('.btn').attr('disabled', false);
                this.hasChanges = true;
            }
        },
        applyChanges: function() {
            var data = this.collectData();
            this.model.get('settings').update({editable: data}, {
                url: '/api/clusters/' + this.model.id + '/attributes',
                success: _.bind(function() {
                    this.hasChanges = false;
                }, this),
                complete: _.bind(function() {
                    this.render();
                    this.model.fetch();
                }, this)
            });
            this.disableControls();
        },
        parseSettings: function(settings) {
            this.tearDownRegisteredSubViews();
            this.$('.settings').html('');
            _.each(_.keys(settings), function(setting) {
                var settingsGroupView = new SettingsGroup({legend: setting, settings: settings[setting], model: this.model, tab: this});
                this.registerSubView(settingsGroupView);
                this.$('.settings').append(settingsGroupView.render().el);
            }, this);
        },
        revertChanges: function() {
            this.parseSettings(this.model.get('settings').get('editable'));
            this.hasChanges = false;
            this.defaultButtonsState(true);
        },
        loadDefaults: function() {
            var defaults = new models.Settings();
            defaults.fetch({
                url: '/api/clusters/' + this.model.id + '/attributes/defaults',
                complete: _.bind(function() {
                    this.parseSettings(defaults.get('editable'));
                    this.checkForChanges();
                }, this)
            });
            this.disableControls();
        },
        render: function () {
            this.$el.html(this.template({cluster: this.model}));
            if (this.model.get('settings').deferred.state() != 'pending') {
                this.parseSettings(this.model.get('settings').get('editable'));
            }
            return this;
        },
        bindTaskEvents: function() {
            var task = this.model.task('deploy', 'running');
            if (task) {
                task.bind('change:status', this.render, this);
                if (this.model.get('settings')) {
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
            if (!this.model.get('settings')) {
                this.model.set({'settings': new models.Settings()}, {silent: true});
                this.model.get('settings').deferred = this.model.get('settings').fetch({
                    url: '/api/clusters/' + this.model.id + '/attributes'
                });
                this.model.get('settings').deferred.done(_.bind(this.render, this));
            }
        }
    });

    SettingsGroup = Backbone.View.extend({
        template: _.template(settingsGroupTemplate),
        className: 'fieldset-group wrapper',
        events: {
            'keyup input[type=text]': 'checkForChanges',
            'change input[type=checkbox], input[type=radio]': 'checkForChanges'
        },
        checkForChanges: function() {
            this.tab.checkForChanges();
        },
        initialize: function(options) {
            _.defaults(this, options);
        },
        render: function() {
            this.$el.html(this.template({settings: this.settings, legend: this.legend, cluster: this.model}));
            return this;
        }
    });

    return SettingsTab;
});
