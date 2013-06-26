casper.start().loadPage('#releases');

casper.then(function() {
    this.test.comment('Testing releases page');
    this.test.assertEvalEquals(function() {return $('.releases-table tbody tr').length}, 2, 'There are two releases presented');
    this.test.assertSelectorAppears('.releases-table .not-available', 'There is unavailable release');
});

casper.run(function() {
    this.test.done();
});
