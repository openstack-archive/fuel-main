casper.start();
casper.createCluster({name: 'Test Cluster'});
casper.loadPage('#cluster/1/nodes').waitForSelector('#tab-nodes > *');
casper.then(function() {
    this.test.comment('Testing cluster page');
    this.test.assertExists('.summary .change-cluster-mode-btn:not(.disabled)', 'Cluster deployment mode is changeable');
    this.test.assertExists('.summary .change-cluster-type-btn:not(.disabled)', 'Cluster type is changeable');
    this.test.assertDoesntExist('.node-list .btn-add-nodes.disabled', 'All "Add Node" buttons are enabled');
    this.test.assertDoesntExist('.node-list .btn-delete-nodes:not(.disabled)', 'All "Delete Node" buttons are disabled');
    this.test.assertExists('.node-list .nodebox.nodeplaceholder', 'Placeholder for controller node presents');

    this.test.comment('Testing cluster deployment mode dialog');
    this.then(function() {
        this.click('.summary .change-cluster-mode-btn');
    });
    this.test.assertSelectorAppears('.modal', 'Cluster deployment mode opens');
    this.then(function() {
        this.test.assertExists('.modal input[type=radio][name=mode][value=simple]:checked', 'Simple deployment mode chosen');
        this.click('.modal input[type=radio][name=mode][value=ha]');
        this.test.assertVisible('.modal input[name=redundancy]', 'Cluster redundancy input is visible if deployment mode is HA');
        this.click('.modal .apply-btn');
    });
    this.test.assertSelectorDisappears('.modal', 'Cluster deployment mode dialog closes after setting deployment mode to HA');
    this.then(function() {
        this.click('.summary .change-cluster-mode-btn');
    });
    this.test.assertSelectorAppears('.modal', 'Cluster deployment mode opens again');
    this.then(function() {
        this.test.assertExists('.modal input[type=radio][name=mode][value=ha]:checked', 'HA deployment mode chosen');
        this.click('.modal input[type=radio][name=mode][value=simple]');
        this.test.assertNotVisible('.modal input[name=redundancy]', 'Cluster redundancy input is not visible if deployment mode is simple');
        this.click('.modal .apply-btn');
    });
    this.test.assertSelectorDisappears('.modal', 'Cluster deployment mode dialog closes after setting deployment mode to simple');
});
casper.run(function() {
    this.test.done();
});
