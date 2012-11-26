var baseUrl = 'http://127.0.0.1:5544/';

casper.loadPage = function(page) {
    return this.thenOpen(baseUrl + page).waitWhileSelector('#content > .loading');
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

casper.createCluster = function(options) {
    options.release = 1;
    return this.thenOpen(baseUrl + 'api/clusters', {
        method: 'post',
        headers: {'Content-Type': 'application/json'},
        data: JSON.stringify(options)
    });
}

casper.createNode = function(options) {
    return this.thenOpen(baseUrl + 'api/nodes', {
        method: 'post',
        headers: {'Content-Type': 'application/json'},
        data: JSON.stringify(options)
    });
}
