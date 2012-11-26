casper.start().loadPage('#releases');

casper.then(function() {
    this.test.comment('Testing releases page');
    this.test.assertSelectorAppears('.table-releases', 'Release list appeared');
    this.test.assertSelectorAppears('.table-releases tbody tr', 'Release list has at least one item');
});

casper.run(function() {
    this.test.done();
});
