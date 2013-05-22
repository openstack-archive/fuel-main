define(function() {
    'use strict';

    var utils = {
        serializeTabOptions: function(options) {
            return _.map(options, function(value, key) {
                return key + ':' + value;
            }).join(',');
        },
        deserializeTabOptions: function(serializedOptions) {
            return _.object(_.map(serializedOptions.split(','), function(option) {
                return option.split(':');
            }));
        },
        urlify: function (text) {
            var urlRegexp = /http:\/\/(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\//g;
            return text.replace(/\n/g, '<br/>').replace(urlRegexp, function(url) {
                return '<a target="_blank" href="' + url + '">' + url + '</a>';
            });
        },
        forceWebkitRedraw: function(el) {
            if (window.isWebkit) {
                el.each(function() {
                    this.style.webkitTransform = 'scale(1)';
                    var dummy = this.offsetHeight;
                    this.style.webkitTransform = '';
                });
            }
        },
        showErrorDialog: function(options, parentView) {
            parentView = parentView || app.page;
            var dialogViews = require('views/dialogs'); // avoid circular dependencies
            var dialog = new dialogViews.SimpleMessage(_.extend({error: true}, options));
            parentView.registerSubView(dialog);
            dialog.render();
        },
        showBandwidth: function(bandwidth) {
            bandwidth = parseInt(bandwidth, 10);
            if (!_.isNumber(bandwidth) || _.isNaN(bandwidth)) {return 'N/A';}
            return (bandwidth / 1000).toFixed(1) + ' Gbps';
        },
        showFrequency: function(frequency) {
            frequency = parseInt(frequency, 10);
            if (!_.isNumber(frequency) || _.isNaN(frequency)) {return 'N/A';}
            var base = 1000;
            var treshold = 1000;
            return(frequency >= treshold ? (frequency / base).toFixed(2) + ' GHz' : frequency + ' MHz');
        },
        showSize: function(bytes, base, treshold) {
            bytes = parseInt(bytes, 10);
            if (!_.isNumber(bytes) || _.isNaN(bytes)) {return 'N/A';}
            base = base || 1024;
            treshold = treshold || 256;
            var units = ['bytes', 'KB', 'MB', 'GB', 'TB'];
            var i, result;
            for (i = 0; i < units.length; i += 1) {
                result = bytes / Math.pow(base, i);
                if (result < treshold) {
                    return (result ? result.toFixed(1) : result) + ' ' + units[i];
                }
            }
            return result;
        },
        showMemorySize: function(bytes) {
            return utils.showSize(bytes, 1024, 1024);
        },
        showDiskSize: function(bytes) {
            return utils.showSize(bytes, 1000);
        }
    };

    return utils;
});
