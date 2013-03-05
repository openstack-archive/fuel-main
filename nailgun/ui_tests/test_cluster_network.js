casper.start();
casper.createCluster({name: 'Test Cluster'});
casper.loadPage('#cluster/1/network').waitForSelector('#tab-network > *');

casper.then(function() {
    this.test.comment('Testing cluster networks: layout rendered');
    this.test.assertEvalEquals(function() {return $('.net-manager input[type=radio]').length}, 2, 'Network manager options are presented');
    this.test.assertEvalEquals(function() {return $('.net-manager input[type=radio]:first:checked').length}, 1, 'Flat DHCP manager is chosen');
    this.test.assertEvalEquals(function() {return $('.networks-table .row').length}, 7, 'All networks are presented');
    this.test.assertDoesntExist('.verify-networks-btn:disabled', 'Verify networks button is enabled');
    this.test.assertExists('.apply-btn:disabled', 'Save networks button is disabled');
});

casper.then(function() {
    this.test.comment('Testing cluster networks: Save button interractions');
    var initialValue = this.evaluate(function(initialValue) {
            return __utils__.getFieldValue('public-cidr');
        });
    this.fill('.networks-table', {'public-cidr': '240.0.1.0/25'});
    this.evaluate(function() {
        $('input[name=public-cidr]').keyup();
    });
    this.test.assertDoesntExist('.apply-btn:disabled', 'Save networks button is enabled if there are changes');
    this.fill('.networks-table', {'public-cidr': initialValue});
    this.evaluate(function() {
        $('input[name=public-cidr]').keyup();
    });
    this.test.assertExists('.apply-btn:disabled', 'Save networks button is disabled again if there are no changes');
});

casper.then(function() {
    this.test.comment('Testing cluster networks: data validation');
    var initialValue = this.evaluate(function(initialValue) {
            return __utils__.getFieldValue('public-cidr');
        });
    this.fill('.networks-table', {'public-cidr': '240.0.1.0/245'});
    this.evaluate(function() {
        $('input[name=public-cidr]').keyup();
    });
    this.test.assertEvalEquals(function() {return $('.networks-table .row:eq(2) .error').length}, 1, 'Field validation has worked');
    this.test.assertExists('.apply-btn:disabled', 'Save networks button is disabled if there is validation error');
    this.fill('.networks-table', {'public-cidr': initialValue});
    this.evaluate(function() {
        $('input[name=public-cidr]').keyup();
    });
    this.test.assertDoesntExist('.networks-table .row:eq(2) .error', 'Field validation works properly');
});

casper.then(function() {
    this.test.comment('Testing cluster networks: change network manager');
    this.click('.net-manager input[type=radio]:not(:checked)');
    this.test.assertEvalEquals(function() {return $('.fixed-row .amount:visible').length}, 1, 'Amount field for a fixed network is presented in VLAN mode');
    this.test.assertEvalEquals(function() {return $('.fixed-row .network_size:visible').length}, 1, 'Size field for a fixed network is presented in VLAN mode');
    this.test.assertExists('.apply-btn:not(:disabled)', 'Save networks button is enabled after manager was changed');
    this.click('.net-manager input[type=radio]:not(:checked)');
    this.test.assertEvalEquals(function() {return $('.fixed-row .amount:visible').length}, 0, 'Amount field was hidden after revert to FlatDHCP');
    this.test.assertEvalEquals(function() {return $('.fixed-row .network_size:visible').length}, 0, 'Size field was hidden after revert to FlatDHCP');
    this.test.assertExists('.apply-btn:disabled', 'Save networks button is disabled again after revert to FlatDHCP');
});

casper.then(function() {
    this.test.comment('Testing cluster networks: save changes');
    this.fill('.networks-table', {'public-cidr': '240.0.1.0/30'});
    this.evaluate(function() {
        $('input[name=public-cidr]').keyup();
    });
    this.click('.apply-btn:not(:disabled)');
    this.waitForSelector('.page-control-error-placeholder');
    this.then(function() {
        this.test.assertEvalEquals(function() {return $('.cidr input.error').length}, 1, 'Changes were not saved due to verification error. An appropriate message is presented and a field with verification error is highlighted');
    });
    this.then(function() {
        this.fill('.networks-table', {'public-cidr': '240.0.1.0/23'});
        this.evaluate(function() {
            $('input[name=public-cidr]').keyup();
        });
        this.click('.apply-btn:not(:disabled)');
        this.test.assertDoesntExist('.page-control-error-placeholder', 'Correct settings were saved successfully');
    });
});

casper.then(function() {
    this.test.comment('Testing cluster networks: verification');
    this.click('.verify-networks-btn:not(:disabled)');
    this.test.assertSelectorAppears('.connect-3-success', 'Verification result is rendered', 10000);
    this.then(function() {
        this.test.assertExists('input:disabled', 'Form fields are disabled while verification');
        this.test.assertEvalEquals(function() {return $('.connect-3-success').length}, 1, 'Verification is in progress');
        this.test.info('Waiting for verification readiness...');
    });
    this.test.assertSelectorDisappears('.connect-3-success', 'Verification result is rendered', 10000);
    this.then(function() {
        this.test.assertEvalEquals(function() {return $('.connect-3-error').length}, 1, 'Verification was failed without nodes in cluster');
        this.test.assertExist('input:not(:disabled)', 'Form fields are enabled again after verification');
    });
});

casper.then(function() {
    this.test.comment('Testing cluster networks: verification task deletion');
    this.fill('.networks-table', {'public-cidr': '240.0.1.0/22'});
    this.evaluate(function() {
        $('input[name=public-cidr]').keyup();
    });
    this.test.assertDoesntExist('.page-control-error-placeholder', 'Verification task was removed after settings has been changed');
});

casper.then(function() {
    this.test.comment('Testing cluster networks: VLAN range fields');
    this.click('.net-manager input[type=radio]:not(:checked)');
    this.fill('.networks-table', {'fixed-amount': '10'});
    this.evaluate(function() {
        $('input[name=fixed-amount]').keyup();
    });
    this.then(function() {
        this.test.assertEvalEquals(function() {return $('.vlan-end:visible').length}, 2, 'VLAN range is displayed');
    });
});

casper.run(function() {
    this.test.done();
});
