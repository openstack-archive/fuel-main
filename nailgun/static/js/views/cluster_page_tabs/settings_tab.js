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
        collectData: function(parentEl, changedData) {
            var model = this, param;
            _.each(parentEl.children('.wrapper'), function(el) {
                if ($(el).data('nested')) {
                    param = $(el).find('h4:first').text();
                    changedData[param] = {};
                    model.collectData($(el), changedData[param]);
                } else {
                    var value;
                    if ($(el).find('input[type=text]').length) {
                        param = $(el).find('input[type=text]');
                        value = param.val();
                    } else if ($(el).find('input[type=checkbox]').length) {
                        param = $(el).find('input[type=checkbox]');
                        value = param.attr('checked') == 'checked' ? true : false;
                    } else {
                        param = $(el).find('select');
                        value = [];
                        _.each(param.children('option'), function(option) {
                            value.push({
                                "id": $(option).attr('value'),
                                "name": $(option).text(),
                                "chosen": $(option).attr('selected') == 'selected' ? true : false
                            });
                        });
                    }
                    changedData[param.attr('name')] = value;
                }
            });
        },
        checkForChanges: function() {
            var changedData = {};
            this.collectData($('.openstack-settings form'), changedData);
            if (_.isEqual(this.model.get('settings').get('editable'), changedData)) {
                this.defaultButtonsState(true);
                this.hasChanges = false;
            } else {
                this.$('.openstack-settings .btn').attr('disabled', false);
                this.hasChanges = true;
            }
        },
        applyChanges: function() {
            var changedData = {};
            this.collectData(this.$('form'), changedData);
            this.model.get('settings').update({editable: changedData}, {
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
            'change input[type=checkbox], select': 'checkForChanges'
        },
        checkForChanges: function() {
            this.tab.checkForChanges();
        },
        initialize: function(options) {
            _.defaults(this, options);
        },
        render: function() {
            this.$el.html(this.template({settings: this.settings, legend: this.legend, cluster: this.model}));
            this.$el.attr('data-nested', !_.isArray(this.settings) && _.isObject(this.settings));
            return this;
        }
    });

    return SettingsTab;
});
