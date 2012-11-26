casper.test.comment('Testing common controls')
casper.start().loadPage('');

casper.then(function() {
    this.test.assertExists('.navigation-bar', 'Navigation bar presents');
    this.test.assertExists('.breadcrumb', 'Breadcrumbs present');
});

casper.run(function() {
    this.test.done();
});
