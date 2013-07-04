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
    this.waitForSelector('.dismiss-settings-dialog');
    this.then(function() {
        this.test.assertExists('.dismiss-settings-dialog', 'Dismiss changes dialog appears if there are changes and user is going to leave the tab');
        this.click('.btn-return');
    });
    this.waitWhileSelector('.dismiss-settings-dialog');
    this.then(function() {
        this.click('.btn-revert-changes');
        this.test.assertExists('.btn-apply-changes:disabled', 'Save settings button is disabled again after changes were cancelled');
    });
});

casper.then(function() {
    this.test.comment('Testing OpenStack settings: save changes');
    this.click('input[type=checkbox]:not(.show-password)');
    this.click('.btn-apply-changes');
    this.waitForSelector('.btn-load-defaults:not(:disabled)');
    this.test.assertExists('.btn-revert-changes:disabled', 'Cancel changes button is disabled after changes were saved successfully');
});

casper.then(function() {
    this.test.comment('Testing OpenStack settings: load defaults');
    this.click('.btn-load-defaults');
    this.test.assertSelectorAppears('.btn-revert-changes:not(:disabled)', 'Cancel changes button is enabled after defaults were loaded', 2000);
    this.then(function() {
        this.test.assertExists('.btn-apply-changes:not(:disabled)', 'Save settings button is enabled after defaults were loaded');
    });
});

casper.run(function() {
    this.test.done();
});
