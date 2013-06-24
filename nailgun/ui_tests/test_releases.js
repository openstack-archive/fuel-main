casper.start().loadPage('#releases');

casper.then(function() {
    this.test.comment('Testing releases page layout');
    this.test.assertEvalEquals(function() {return $('.releases-table tbody tr').length}, 2, 'There are two releases presented');
    this.test.assertSelectorAppears('.releases-table .not-available', 'There is unavailable release');
});

casper.then(function() {
    this.test.comment('Testing release downloading');
    this.click('.btn-rhel-setup');
    this.test.assertSelectorAppears('.modal', 'RHEL credentials popup appears');
    this.then(function() {
        this.test.assertExists('.modal input[value=rhsm]:checked', 'RHSM license type is chosen');
        this.test.assertEvalEquals(function() {return $('.modal fieldset input:visible').length}, 2, 'RHSM license type credentials fields are presented');
        this.click('.modal input[type=radio]:not(:checked)');
        this.test.assertExists('.modal input[value=rhn]:checked', 'RHN license type is chosen');
        this.test.assertEvalEquals(function() {return $('.modal fieldset input').length}, 4, 'RHN license type credentials fields are presented');
        this.click('.modal .btn-os-download');
        this.test.assertEvalEquals(function() {return $('.modal .control-group.error').length}, 4, 'Empty fields validation has worked');
        this.click('.modal input[type=radio]:not(:checked)');
        this.fill('.modal form.rhel-license', {'username': 'rheltest', 'password': 'password'});
        this.click('.modal .btn-os-download');
        this.test.assertExists('.modal .alert', 'Credentials validation works');
        this.fill('.modal form.rhel-license', {'username': 'username', 'password': 'password'});
        this.click('.modal .btn-os-download');
    });
    this.test.assertSelectorDisappears('.modal', 'RHEL credentials popup was closed');
    this.then(function() {
        this.test.assertSelectorAppears('.progress', 'RHEL downloading started');
        this.waitWhileSelector('.progress');
    });
    this.then(function() {
        this.test.assertDoesntExist('.releases-table .not-available', 'RHEL downloading was finished');
    });
});

casper.run(function() {
    this.test.done();
});
