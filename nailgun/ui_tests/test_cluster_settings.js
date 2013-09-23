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
casper.start();
casper.createCluster({name: 'Test Cluster'});
casper.loadPage('#cluster/1/settings').waitForSelector('#tab-settings > *');

casper.then(function() {
    this.test.comment('Testing cluster OpenStack settings');
    this.test.assertExists('.btn-load-defaults:not(:disabled)', 'Load defaults button is enabled');
    this.test.assertExists('.btn-revert-changes:disabled', 'Cancel changes button is disabled');
    this.test.assertExists('.btn-apply-changes:disabled', 'Save settings button is disabled');
});

casper.then(function() {
    this.test.comment('Testing cluster OpenStack settings: Save button interractions');
    this.click('input[type=checkbox]:not(.show-password)');
    this.test.assertExists('.btn-apply-changes:not(:disabled)', 'Save settings button is enabled if there are changes');
    this.click('input[type=checkbox]:not(.show-password)');
    this.test.assertExists('.btn-apply-changes:disabled', 'Save settings button is disabled again if there are no changes');
});

casper.then(function() {
    this.test.comment('Testing cluster OpenStack settings: cancel changes operation');
    this.click('input[type=checkbox]:not(.show-password)');
    this.click('.nav-tabs li.active + li a');
    this.test.assertSelectorAppears('.dismiss-settings-dialog', 'Dismiss changes dialog appears if there are changes and user is going to leave the tab');
    this.then(function() {
        this.click('.btn-return');
    });
    this.test.assertSelectorDisappears('.dismiss-settings-dialog', 'Dismiss changes dialog was closed');
    this.then(function() {
        this.click('.btn-revert-changes');
        this.test.assertExists('.btn-apply-changes:disabled', 'Save settings button is disabled again after changes were cancelled');
    });
});

casper.then(function() {
    this.test.comment('Testing OpenStack settings: save changes');
    this.click('input[type=checkbox]:not(.show-password)');
    this.click('.btn-apply-changes');
    this.waitWhileSelector('.btn-load-defaults:disabled');
    this.then(function() {
        this.test.assertExists('.btn-revert-changes:disabled', 'Cancel changes button is disabled after changes were saved successfully');
    });
});

casper.then(function() {
    this.test.comment('Testing OpenStack settings: load defaults');
    this.click('.btn-load-defaults');
    this.waitWhileSelector('.btn-load-defaults:disabled');
    this.then(function() {
        this.test.assertExists('.btn-revert-changes:not(:disabled)', 'Cancel changes button is enabled after defaults were loaded');
        this.test.assertExists('.btn-apply-changes:not(:disabled)', 'Save settings button is enabled after defaults were loaded');
    });
});

casper.run(function() {
    this.test.done();
});
