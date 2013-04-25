casper.start();
casper.createCluster({name: 'Test Cluster'});
casper.loadPage('#cluster/1/network').waitForSelector('#tab-network > *');

casper.then(function() {
    this.test.comment('Testing cluster networks: layout rendered');
    this.test.assertEvalEquals(function() {return $('.net-manager input[type=radio]').length}, 2, 'Network manager options are presented');
    this.test.assertExists('.net-manager input[value=FlatDHCPManager]:checked', 'Flat DHCP manager is chosen');
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
    this.test.assertExists('.control-group.error', 'Field validation has worked');
    this.test.assertExists('.apply-btn:disabled', 'Save networks button is disabled if there is validation error');
    this.fill('.networks-table', {'public-cidr': initialValue});
    this.evaluate(function() {
        $('input[name=public-cidr]').keyup();
    });
    this.test.assertDoesntExist('.control-group.error', 'Field validation works properly');
});

casper.then(function() {
    this.test.comment('Check Amount field validation');
    this.click('.net-manager input[type=radio]:not(:checked)');
    this.test.assertExists('.net-manager input[value=VlanManager]:checked', 'VLAN manager is chosen');
    var initialAmountValue = this.evaluate(function(initialValue) {
        return __utils__.getFieldValue('fixed-amount');
    });
    var initialVlanIDValue = this.evaluate(function(initialValue) {
        return __utils__.getFieldValue('fixed-vlan_start');
    });

    casper.then(function() {
	this.fill('.networks-table', {'fixed-amount': ' '});
	this.evaluate(function() {
	    $('input[name=fixed-amount]').keyup();
	});
	this.test.assertExists('.control-group.error', 'Field validation has worked with empty field');
	this.test.assertExists('.apply-btn:disabled', 'Save networks button is disabled if there is validation error');
    });

    casper.then(function() {
        this.fill('.networks-table', {'fixed-amount': '-10'});
        this.evaluate(function() {
            $('input[name=fixed-amount]').keyup();
        });
        this.test.assertExists('.control-group.error', 'Field validation has worked when use negative number');
        this.test.assertExists('.apply-btn:disabled', 'Save networks button is disabled if there is validation error');
    });

    casper.then(function() {
	this.fill('.networks-table', {'fixed-amount': '0'});
        this.evaluate(function() {
            $('input[name=fixed-amount]').keyup();
        });
	this.test.assertExists('.control-group.error', 'Field validation has worked when use 0');
        this.test.assertExists('.apply-btn:disabled', 'Save networks button is disabled if there is validation error');
    });

    casper.then(function() {
	this.fill('.networks-table', {
            'fixed-amount': '2',
            'fixed-vlan_start': '4094'
        });
        this.evaluate(function() {
            $('input[name=fixed-amount]').keyup();
        });
	this.test.assertExists('.control-group.error', 'Field validation has worked if amount more than 4095 - VLAN ID');
        this.test.assertExists('.apply-btn:disabled', 'Save networks button is disabled if there is validation error');
    });

    casper.then(function() {
	this.fill('.networks-table', {
            'fixed-amount': '1',
            'fixed-vlan_start': '4094'
        });
        this.evaluate(function() {
            $('input[name=fixed-amount]').keyup();
        });
        this.test.assertDoesntExist('.control-group.error', 'Field validation works properly');
        this.test.assertDoesntExist('.networks-table.fixed-vlan-end', 'Field end vlan value works properly');
    });

    casper.then(function() {
        this.fill('.networks-table', {
            'fixed-amount': '2',
            'fixed-vlan_start': '4093'
        });
        this.evaluate(function() {
            $('input[name=fixed-amount]').keyup();
        });
	this.test.assertEvalEquals(function() {return $('input[name=fixed-vlan-end]').val()}, '4094', 'End value is correct');
        this.test.assertDoesntExist('.control-group.error', 'Field validation works properly');
    });

    casper.then(function() {
        this.fill('.networks-table', {
            'fixed-amount': '4094',
            'fixed-vlan_start': '1'
        });
        this.evaluate(function() {
            $('input[name=fixed-amount]').keyup();
        });
	this.test.assertEvalEquals(function() {return $('input[name=fixed-vlan-end]').val()}, '4094', 'End value is correct');
        this.test.assertDoesntExist('.control-group.error', 'Field validation works properly');
    });

    casper.then(function() {
        this.fill('.networks-table', {
            'fixed-amount': '10',
            'fixed-vlan_start': '250'
        });
        this.evaluate(function() {
            $('input[name=fixed-amount]').keyup();
        });
	this.test.assertEvalEquals(function() {return $('input[name=fixed-vlan-end]').val()}, '259', 'End value is correct');
        this.test.assertDoesntExist('.control-group.error', 'Field validation works properly');
    });

    casper.then(function() {
        this.fill('.networks-table', {
            'fixed-amount': initialAmountValue,
            'fixed-vlan_start': initialVlanIDValue
        });
        this.click('.net-manager input[type=radio]:not(:checked)');
    });

});

casper.then(function() {
    this.test.comment('Check CIDR field validation');
    var initialCIDRValue = this.evaluate(function(initialValue) {
        return __utils__.getFieldValue('public-cidr');
    });

    casper.then(function() {
        this.fill('.networks-table', {'public-cidr': ' '});
        this.evaluate(function() {
            $('input[name=public-cidr]').keyup();
        });
	this.test.assertExists('.control-group.error', 'Field validation has worked properly in case of empty field');
    });

    casper.then(function() {
	this.fill('.networks-table', {'public-cidr': '0.10.-1.255/15'});
        this.evaluate(function() {
            $('input[name=public-cidr]').keyup();
        });
	this.test.assertExists('.control-group.error', 'Field validation has worked properly in case of negative number -1');
    });

    casper.then(function() {
	this.fill('.networks-table', {'public-cidr': '0.-100.240.255/15'});
        this.evaluate(function() {
            $('input[name=public-cidr]').keyup();
        });
	this.test.assertExists('.control-group.error', 'Field validation has worked properly in case of negative number -100');
    });

    casper.then(function() {
	this.fill('.networks-table', {'public-cidr': '0.256.240.255/15'});
        this.evaluate(function() {
            $('input[name=public-cidr]').keyup();
        });
	this.test.assertExists('.control-group.error', 'Field validation has worked properly in case of number out of area 255');
    });

    casper.then(function() {
	this.fill('.networks-table', {'public-cidr': '0.750.240.255/15'});
        this.evaluate(function() {
            $('input[name=public-cidr]').keyup();
        });
	this.test.assertExists('.control-group.error', 'Field validation has worked properly in case of number 750');
    });

    casper.then(function() {
	this.fill('.networks-table', {'public-cidr': '0.01.240.255/15'});
        this.evaluate(function() {
            $('input[name=public-cidr]').keyup();
        });
	this.test.assertExists('.control-group.error', 'Field validation has worked properly in case of number starts with 0');
    });

    casper.then(function() {
	this.fill('.networks-table', {'public-cidr': '0.000.240.255/15'});
        this.evaluate(function() {
            $('input[name=public-cidr]').keyup();
        });
	this.test.assertExists('.control-group.error', 'Field validation has worked properly in case of number 000');
    });

    casper.then(function() {
	this.fill('.networks-table', {'public-cidr': '0.50.240.255.45/15'});
        this.evaluate(function() {
            $('input[name=public-cidr]').keyup();
        });
	this.test.assertExists('.control-group.error', 'Field validation has worked properly in case of big amount of decimals groups');
    });

    casper.then(function() {
	this.fill('.networks-table', {'public-cidr': '0.240.255/15'});
        this.evaluate(function() {
            $('input[name=public-cidr]').keyup();
        });
	this.test.assertExists('.control-group.error', 'Field validation has worked properly in case of little amount of decimals groups');
    });

    casper.then(function() {
	this.fill('.networks-table', {'public-cidr': '0.1000.240.255/15'});
        this.evaluate(function() {
            $('input[name=public-cidr]').keyup();
        });
	this.test.assertExists('.control-group.error', 'Field validation has worked properly in case of bigger number of symbols in group');
    });

    casper.then(function() {
	this.fill('.networks-table', {'public-cidr': '0..240.255/15'});
        this.evaluate(function() {
            $('input[name=public-cidr]').keyup();
        });
	this.test.assertExists('.control-group.error', 'Field validation has worked properly in case of any empty group');
    });

    casper.then(function() {
	this.fill('.networks-table', {'public-cidr': '0.10.100.255/15'});
        this.evaluate(function() {
            $('input[name=public-cidr]').keyup();
        });
        this.test.assertDoesntExist('.control-group.error', 'Validation error description disappears if there are no errors');
    });

    casper.then(function() {
	this.fill('.networks-table', {'public-cidr': initialCIDRValue});
        this.evaluate(function() {
            $('input[name=public-cidr]').keyup();
        });
    });

});

casper.then(function() {
    this.test.comment('Check CIDR prefix');
    var initialCIDRValue = this.evaluate(function(initialValue) {
        return __utils__.getFieldValue('public-cidr');
    });

    casper.then(function() {
	this.fill('.networks-table', {'public-cidr': '240.0.1.0/1'});
        this.evaluate(function() {
            $('input[name=public-cidr]').keyup();
        });
	this.test.assertExists('.control-group.error', 'Field validation has worked properly in case of prefix "1"');
    });

    casper.then(function() {
	this.fill('.networks-table', {'public-cidr': '240.0.1.0/-10'});
        this.evaluate(function() {
            $('input[name=public-cidr]').keyup();
        });
	this.test.assertExists('.control-group.error', 'Field validation has worked properly in case of prefix "-10"');
    });

    casper.then(function() {
	this.fill('.networks-table', {'public-cidr': '240.0.1.0/0'});
        this.evaluate(function() {
            $('input[name=public-cidr]').keyup();
        });
	this.test.assertExists('.control-group.error', 'Field validation has worked properly in case of prefix "0"');
    });


    casper.then(function() {
	this.fill('.networks-table', {'public-cidr': '240.0.1.0/31'});
        this.evaluate(function() {
            $('input[name=public-cidr]').keyup();
        });
	this.test.assertExists('.control-group.error', 'Field validation has worked properly in case of prefix "31"');
    });

    casper.then(function() {
	this.fill('.networks-table', {'public-cidr': '240.0.1.0/75'});
        this.evaluate(function() {
            $('input[name=public-cidr]').keyup();
        });
	this.test.assertExists('.control-group.error', 'Field validation has worked properly in case of prefix "75"');
    });

    casper.then(function() {
	this.fill('.networks-table', {'public-cidr': '240.0.1.0/test'});
        this.evaluate(function() {
            $('input[name=public-cidr]').keyup();
        });
	this.test.assertExists('.control-group.error', 'Field validation has worked properly in case of prefix "test"');
    });

    casper.then(function() {
	this.fill('.networks-table', {'public-cidr': '240.0.1.0/2'});
        this.evaluate(function() {
            $('input[name=public-cidr]').keyup();
        });
        this.test.assertDoesntExist('.control-group.error', 'Field validation works properly in case of no errors (prefix "2")');
    });

    casper.then(function() {
	this.fill('.networks-table', {'public-cidr': '240.0.1.0/30'});
        this.evaluate(function() {
            $('input[name=public-cidr]').keyup();
        });
        this.test.assertDoesntExist('.control-group.error', 'Field validation works properly in case of no errors (prefix "30")');
    });

    casper.then(function() {
	this.fill('.networks-table', {'public-cidr': '240.0.1.0/15'});
        this.evaluate(function() {
            $('input[name=public-cidr]').keyup();
        });
        this.test.assertDoesntExist('.control-group.error', 'Field validation works properly in case of no errors (prefix "15")');
    });

    casper.then(function() {
	this.fill('.networks-table', {'public-cidr': initialCIDRValue});
        this.evaluate(function() {
            $('input[name=public-cidr]').keyup();
        });
    });
});

casper.then(function() {
    this.test.comment('Check VlanID field validation');
    var initialVlanIDValue = this.evaluate(function(initialValue) {
        return __utils__.getFieldValue('public-vlan_start');
    });

    casper.then(function() {
	this.fill('.networks-table', {'public-vlan_start': '0'});
	this.evaluate(function() {
	    $('input[name=public-vlan_start]').keyup();
	});
        this.test.assertExists('.control-group.error', 'Field validation has worked properly in case of 0 value');
    });

    casper.then(function() {
        this.fill('.networks-table', {'public-vlan_start': '4095'});
        this.evaluate(function() {
                $('input[name=public-vlan_start]').keyup();
        });
        this.test.assertExists('.control-group.error', 'Field validation has worked properly in case of 4095 value');
    });

    casper.then(function() {
        this.fill('.networks-table', {'public-vlan_start': '-100'});
        this.evaluate(function() {
                $('input[name=public-vlan_start]').keyup();
        });
        this.test.assertExists('.control-group.error', 'Field validation has worked properly in case of -100 value');
    });

    casper.then(function() {
        this.fill('.networks-table', {'public-vlan_start': '5000'});
        this.evaluate(function() {
            $('input[name=public-vlan_start]').keyup();
        });
        this.test.assertExists('.control-group.error', 'Field validation has worked properly in case of 5000 value');
    });

    casper.then(function() {
        this.fill('.networks-table', {'public-vlan_start': '1'});
        this.evaluate(function() {
            $('input[name=public-vlan_start]').keyup();
        });
        this.test.assertDoesntExist('.control-group.error', 'No validation errors in case of 1 value');
    });

    casper.then(function() {
        this.fill('.networks-table', {'public-vlan_start': '4094'});
        this.evaluate(function() {
            $('input[name=public-vlan_start]').keyup();
        });
        this.test.assertDoesntExist('.control-group.error', 'No validation errors in case of 4094 value');
    });

    casper.then(function() {
        this.fill('.networks-table', {'public-vlan_start': '2000'});
        this.evaluate(function() {
            $('input[name=public-vlan_start]').keyup();
        });
        this.test.assertDoesntExist('.control-group.error', 'No validation errors in case of 2000 value');
    });

    casper.then(function() {
        this.fill('.networks-table', {'public-vlan_start': initialVlanIDValue});
        this.evaluate(function() {
            $('input[name=public-vlan_start]').keyup();
        });
    });
});

casper.then(function() {
    this.test.comment('Testing cluster networks: change network manager');
    this.click('.net-manager input[type=radio]:not(:checked)');
    this.test.assertDoesntExist('.fixed-row dive.hide', 'Amount and size fields for a fixed network are presented in VLAN mode');
    this.test.assertExists('.apply-btn:not(:disabled)', 'Save networks button is enabled after manager was changed');
    this.click('.net-manager input[type=radio]:not(:checked)');
    this.test.assertDoesntExist('.fixed-row .amount:visible', 'Amount field was hidden after revert to FlatDHCP');
    this.test.assertDoesntExist('.fixed-row .network_size:visible', 'Size field was hidden after revert to FlatDHCP');
    this.test.assertExists('.apply-btn:disabled', 'Save networks button is disabled again after revert to FlatDHCP');
});

casper.then(function() {
    this.test.comment('Testing cluster networks: save changes');
    this.fill('.networks-table', {'public-cidr': '240.0.1.0/23'});
    this.evaluate(function() {
        $('input[name=public-cidr]').keyup();
    });
    this.click('.apply-btn:not(:disabled)');
    this.waitForSelector('input:not(:disabled)');
    this.then(function() {
        this.test.assertDoesntExist('.alert-error', 'Correct settings were saved successfully');
    });
});

casper.then(function() {
    this.test.comment('Testing cluster networks: verification');
    this.click('.verify-networks-btn:not(:disabled)');
    this.test.assertSelectorAppears('.connect-3-success', 'Verification result is rendered', 10000);
    this.then(function() {
        this.test.assertExists('input:disabled', 'Form fields are disabled while verification');
        this.test.assertExists('.connect-3-success', 'Verification is in progress');
        this.test.info('Waiting for verification readiness...');
    });
    this.test.assertSelectorDisappears('.connect-3-success', 'Verification result is rendered', 10000);
    this.then(function() {
        this.test.assertExists('.connect-3-error', 'Verification was failed without nodes in cluster');
        this.test.assertExists('input:not(:disabled)', 'Form fields are enabled again after verification');
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
        this.test.assertDoesntExist('.vlan_start .hide', 'VLAN range is displayed');
    });
});

casper.run(function() {
    this.test.done();
});
