casper.start().loadPage('');

casper.then(function() {
    this.test.comment('Testing common controls');
    this.test.assertSelectorAppears('.navigation-bar', 'Navigation bar presents');
    this.test.assertSelectorAppears('.breadcrumb', 'Breadcrumbs present');
});

casper.run(function() {
    this.test.done();
});
