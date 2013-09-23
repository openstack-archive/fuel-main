/*
 * Copyright 2013 Mirantis, Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use this file except in compliance with the License. You may obtain
 * a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations
 * under the License.
**/
define(['require'], function(require) {
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
        linebreaks: function(text) {
            return text.replace(/\n/g, '<br/>');
        },
        composeLink: function(url) {
            return '<a target="_blank" href="' + url + '">' + url + '</a>';
        },
        urlify: function (text) {
            var urlRegexp = /(?:https?:\/\/([\-\w\.]+)+(:\d+)?(\/([\w\/_\.]*(\?\S+)?)?)?)/g;
            return utils.linebreaks(text).replace(urlRegexp, utils.composeLink);
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
            var dialog = new dialogViews.Dialog();
            parentView.registerSubView(dialog);
            dialog.displayInfoMessage(_.extend({error: true, message: ''}, options));
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
        showSize: function(bytes, treshold) {
            bytes = parseInt(bytes, 10);
            if (!_.isNumber(bytes) || _.isNaN(bytes)) {return 'N/A';}
            var base = 1024;
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
            return utils.showSize(bytes, 1024);
        },
        showDiskSize: function(value, power) {
            power = power || 0;
            return utils.showSize(value * Math.pow(1024, power));
        },
        calculateNetworkSize: function(cidr) {
            return Math.pow(2, 32 - parseInt(_.last(cidr.split('/')), 10));
        },
        formatNumber: function(n) {
            return String(n).replace(/\d/g, function(c, i, a) {
                return i > 0 && c !== '.' && (a.length - i) % 3 === 0 ? ',' + c : c;
            });
        },
        floor: function(n, decimals) {
            return Math.floor(n * Math.pow(10, decimals)) / Math.pow(10, decimals);
        }
    };

    return utils;
});
