casper.loadPage = function(page) {
    var baseUrl = 'http://127.0.0.1:5544/';
    return this.open(baseUrl + page).waitWhileSelector('#content > .loading');
}

casper.test.assertSelectorAppears = function(selector, message, timeout) {
    return this.casper.waitForSelector(selector, function () {
        this.test.pass(message);
    }, function() {
        this.test.fail(message);
    }, timeout);
}

casper.test.assertSelectorDisappears = function(selector, message, timeout) {
    return this.casper.waitWhileSelector(selector, function () {
        this.test.pass(message);
    }, function() {
        this.test.fail(message);
    }, timeout);
}
