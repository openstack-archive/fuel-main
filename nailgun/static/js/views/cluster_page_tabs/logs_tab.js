define(
[
    'models',
    'views/common',
    'text!templates/cluster/logs_tab.html',
    'text!templates/cluster/log_entry.html'
],
function(models, commonViews, logsTabTemplate, logEntryTemplate) {
    'use strict';

    var LogsTab = commonViews.Tab.extend({
        updateInterval: 5000,
        reversed: true,
        template: _.template(logsTabTemplate),
        logEntryTemplate: _.template(logEntryTemplate),
        events: {
            'click .show-logs-btn:not(.disabled)': 'onShowButtonClick',
            'click .show-more-entries': 'onShowMoreClick',
            'click .show-all-entries': 'onShowAllClick',
            'change select': 'updateShowButtonState',
            'change select[name=type]': 'onTypeChange',
            'change select[name=node]': 'onNodeChange',
            'change select[name=source]': 'updateLevels'
        },
        beforeTearDown: function() {
            if (this.timeout) {
                clearTimeout(this.timeout);
            }
        },
        scheduleUpdate: function() {
            this.timeout = _.delay(_.bind(this.update, this), this.updateInterval);
        },
        update: function() {
            this.fetchLogs({from: this.from}, {
                success: _.bind(function(data) {
                    this.appendLogEntries(data, false);
                }, this),
                complete: _.bind(this.scheduleUpdate, this)
            });
        },
        onTypeChange: function() {
            var chosenType = this.$('select[name=type]').val();
            this.$('.log-node-filter').toggle(chosenType == 'remote');
            this.fetchSources(chosenType);
        },
        onNodeChange: function() {
            this.fetchSources('remote');
        },
        fetchSources: function(type) {
            var input = this.$('select[name=source]');
            this.$('select[name=source], select[name=level]').html('').attr('disabled', true);
            this.updateShowButtonState();
            this.sources = new models.LogSources();
            if (type == 'remote') {
                this.sources.deferred = this.sources.fetch({url: '/api/logs/sources/nodes/' + this.$('select[name=node]').val()});
            } else if (!this.model.get('log_sources')) {
                this.sources.deferred = this.sources.fetch();
                this.sources.deferred.done(_.bind(function() {
                    this.model.set('log_sources', this.sources.toJSON());
                }, this));
            } else {
                this.sources.reset(this.model.get('log_sources'));
                this.sources.deferred = $.Deferred();
                this.sources.deferred.resolve();
            }
            this.sources.deferred.done(_.bind(type == 'local' ? this.updateLocalSources : this.updateRemoteSources, this));
            this.sources.deferred.done(_.bind(function() {
                if (this.sources.length) {
                    input.attr('disabled', false);
                    this.updateShowButtonState();
                    this.updateLevels();
                }
            }, this));
            this.sources.deferred.fail(_.bind(function() {
                this.$('.node-sources-error').show();
            }, this));
            return this.sources.deferred;
        },
        updateSources: function() {
            var chosenType = this.$('select[name=type]').val();
            if (chosenType == 'local') {
                this.updateLocalSources();
            } else {
                this.updateRemoteSources();
            }
        },
        updateLocalSources: function() {
            var input = this.$('select[name=source]');
            this.sources.each(function(source) {
                if (!source.get('remote')) {
                    input.append($('<option/>', {value: source.id, text: source.get('name')}));
                }
            });
        },
        updateRemoteSources: function() {
            var input = this.$('select[name=source]');
            var groups = [''], sourcesByGroup = {'': []};
            this.sources.each(function(source) {
                var group = source.get('group') || '';
                if (!_.has(sourcesByGroup, group)) {
                    sourcesByGroup[group] = [];
                    groups.push(group);
                }
                sourcesByGroup[group].push(source);
            });
            _.each(groups, function(group) {
                if (sourcesByGroup[group].length) {
                    var el = group ? $('<optgroup/>', {label: group}).appendTo(input) : input;
                    _.each(sourcesByGroup[group], function(source) {
                        el.append($('<option/>', {value: source.id, text: source.get('name')}));
                    });
                }
            });
        },
        updateLevels: function() {
            var input = this.$('select[name=level]');
            var chosenSourceId = this.$('select[name=source]').val();
            if (chosenSourceId) {
                input.html('').attr('disabled', false);
                var source = this.sources.get(chosenSourceId);
                _.each(source.get('levels'), function(level) {
                    input.append($('<option/>').text(level));
                }, this);
            }
        },
        updateShowButtonState: function() {
            this.$('.show-logs-btn').toggleClass('disabled', !this.$('select[name=source]').val());
        },
        onShowButtonClick: function() {
            this.showLogs({truncate_log: true});
        },
        onShowMoreClick: function(e) {
            var count = parseInt($(e.currentTarget).text(), 10) + this.$('.table-logs .log-entries tr').length;
            this.showLogs({truncate_log: true, max_entries: count});
        },
        onShowAllClick: function() {
            this.showLogs({});
        },
        fetchLogs: function(data, callbacks) {
            var options = {
                url: '/api/logs',
                dataType: 'json',
                data: {
                    node: this.chosenNodeId,
                    source: this.chosenSourceId,
                    level: this.chosenLevel
                }
            };
            _.extend(options, callbacks);
            _.extend(options.data, data);
            return $.ajax(options);
        },
        showLogs: function(params) {
            if (this.timeout) {
                clearTimeout(this.timeout);
            }
            this.from = 0;

            this.chosenType = this.$('select[name=type]').val();
            this.chosenNodeId = this.$('select[name=node]').val();
            this.chosenSourceId = this.$('select[name=source]').val();
            this.chosenLevel = this.$('select[name=level]').val();

            var options = this.getOptions();
            this.model.set({'log_options': options}, {silent: true});
            app.navigate('#cluster/' + this.model.id + '/logs/' + this.serializeOptions(options), {trigger: false, replace: true});

            this.$('.logs-fetch-error, .node-sources-error').hide();
            if (!this.reversed) {
                this.$('.table-logs').hide();
            } else {
                this.$('.table-logs .entries-skipped-msg').hide();
            }
            this.$('.logs-loading').show();
            this.$('select').attr('disabled', true);
            this.$('.show-logs-btn').addClass('disabled');

            this.fetchLogs(params, {
                complete: _.bind(function() {
                    this.$('.logs-loading').hide();
                    this.$('select').attr('disabled', false);
                }, this),
                success: _.bind(function(data) {
                    this.$('.table-logs .log-entries').html('');
                    if (data.entries.length) {
                        if (data.entries_skipped) {
                            this.showEntriesSkippedMsg(data.entries_skipped);
                        } else {
                            this.$('.table-logs .entries-skipped-msg').hide();
                        }
                        this.appendLogEntries(data, true);
                    } else {
                        this.$('.table-logs .no-logs-msg').show();
                        this.$('.table-logs .entries-skipped-msg').hide();
                    }
                    this.$('.table-logs').show();
                    this.scheduleUpdate();
                }, this),
                error: _.bind(function() {
                    this.$('.logs-fetch-error').show();
                    this.$('.show-logs-btn').removeClass('disabled');
                }, this)
            });
        },
        showEntriesSkippedMsg: function(entriesCount) {
            var el = this.$('.table-logs .entries-skipped-msg');
            el.show();
            el.find('.entries-count').text(entriesCount);
            el.find('.show-more-entries').remove();
            _.each([100, 500, 1000, 5000, 10000], function(count) {
                if (count < entriesCount) {
                    el.find('.show-all-entries').before($('<span/>', {'class': 'show-more-entries', text: count}));
                }
            }, this);
        },
        appendLogEntries: function(data, doNotScroll) {
            this.from = data.from;
            if (data.entries.length) {
                if (this.reversed) {
                    data.entries.reverse();
                }
                // autoscroll only if window is already scrolled to bottom
                var scrollToBottom = !this.reversed && !doNotScroll && $(document).height() == $(window).scrollTop() + $(window).height();

                this.$('.table-logs .no-logs-msg').hide();
                this.$('.table-logs .log-entries')[this.reversed ? 'prepend' : 'append'](_.map(data.entries, function(entry) {
                    return this.logEntryTemplate({entry: entry});
                }, this).join(''));

                if (scrollToBottom) {
                    $(window).scrollTop($(document).height());
                }
            }
        },
        serializeOptions: function(options) {
            return _.map(options, function(value, key) {
                return key + ':' + value;
            }).join(',');
        },
        deserializeOptions: function(serializedOptions) {
            return _.object(_.map(serializedOptions.split(','), function(option) {
                return option.split(':');
            }));
        },
        getOptions: function() {
            var options = {};
            options.type = this.chosenType;
            if (options.type == 'remote') {
                options.node = this.chosenNodeId;
            }
            options.source = this.chosenSourceId;
            options.level = this.chosenLevel.toLowerCase();
            return options;
        },
        initialize: function(params) {
            _.defaults(this, params);
            this.from = 0;
            this.sources = new models.LogSources();
            this.types = [['local', 'Admin node']];
            if (this.model.get('nodes').length) {
                this.types.push(['remote', 'Other servers']);
            }
        },
        render: function() {
            this.$el.html(this.template({
                cluster: this.model,
                types: this.types,
                chosenType: this.chosenType,
                chosenNodeId: this.chosenNodeId,
                chosenSourceId: this.chosenSourceId
            }));
            if (this.reversed) {
                this.$('.table-logs').append(this.$('.table-logs .entries-skipped-msg').detach());
            }
            if (!this.sourcesFetched) {
                this.sourcesFetched = true;
                // this part is run on first rendering only
                var options = {};
                if (this.tabOptions) {
                    options = this.deserializeOptions(this.tabOptions);
                } else if (this.model.get('log_options')) {
                    options = this.model.get('log_options');
                }
                _.each(['type', 'node'], function(option) {
                    if (options[option]) {
                        this.$('select[name=' + option + ']').val(options[option]);
                    }
                }, this);
                this.$('select[name=type]').trigger('change'); // starts to fetch sources
                if (options.source) {
                    this.sources.deferred.done(_.bind(function() {
                        this.$('select[name=source]').val(options.source).trigger('change');
                        if (options.level) {
                            this.$('select[name=level]').val(options.level.toUpperCase());
                        }
                    }, this));
                }
                if (_.keys(options).length) {
                    this.sources.deferred.done(_.bind(function() {
                        this.$('.show-logs-btn:not(.disabled)').click();
                    }, this));
                }
            } else {
                this.updateSources();
                this.updateShowButtonState();
            }
            return this;
        }
    });

    return LogsTab;
});
