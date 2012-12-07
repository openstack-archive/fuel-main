casper.start();
casper.createCluster({name: 'Test Cluster'});
casper.createNode({status: 'ready', mac: '84:AA:B8:E6:30:F0', cluster_id: 1});
casper.loadPage('#cluster/1/logs').waitForSelector('#tab-logs > *');
casper.then(function() {
    this.test.comment('Testing logs tab');
    this.test.assertSelectorAppears('.filter-bar select[name=node] option', 'Node selection box appears and is not empty');
    this.test.assertSelectorAppears('.filter-bar select[name=source] option', 'Log source selection box appears and is not empty');
    this.test.assertSelectorAppears('.filter-bar .show-logs-btn:not([disabled])', '"Show logs" button is available');
});

casper.run(function() {
    this.test.done();
});
