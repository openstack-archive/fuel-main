casper.start().loadPage('#clusters');

casper.then(function() {
    this.test.comment('Testing cluster list page');
    this.test.assertExists('.cluster-list', 'Cluster container exists');
    this.test.assertExists('.create-cluster', 'Cluster creation control exists');
});

casper.then(function() {
    this.test.comment('Testing cluster creation');
    var name = 'Test Cluster';
    this.click('.create-cluster');
    this.test.assertSelectorAppears('.modal', 'Cluster creation dialog opens');
    this.test.assertSelectorAppears('.modal form select[name=release] option', 'Release select box updates with releases');
    this.then(function() {
        this.fill('.modal form', {name: name});
        this.click('.create-cluster-btn');
    });
    this.test.assertSelectorDisappears('.modal', 'Cluster creation dialog closes after from submission');
    this.test.assertSelectorAppears('.cluster-list a.clusterbox', 'Created cluster appears in list');
    this.then(function() {
        this.test.assertSelectorHasText('.cluster-list a.clusterbox .cluster-name', name, 'Created cluster has specified name');
    })
});

casper.run(function() {
    this.test.done();
});
