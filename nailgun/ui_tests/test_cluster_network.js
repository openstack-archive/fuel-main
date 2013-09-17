/*
 * Copyright 2013 Mirantis, Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use this file except in compliance with the License. You may obtain
 * a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations
 * under the License.
**/
casper.start();
casper.createCluster({name: 'Test Cluster'});
casper.loadPage('#cluster/1/network').waitForSelector('#tab-network > *');

casper.then(function() {
    this.test.comment('Testing cluster networks: layout rendered');
    this.test.assertEvalEquals(function() {return $('.net-manager input[type=radio]').length}, 2, 'Network manager options are presented');
    this.test.assertExists('.net-manager input[value=FlatDHCPManager]:checked', 'Flat DHCP manager is chosen');
    this.test.assertEvalEquals(function() {return $('legend.networks').length}, 5, 'All networks are presented');
    this.test.assertDoesntExist('.verify-networks-btn:disabled', 'Verify networks button is enabled');
    this.test.assertExists('.apply-btn:disabled', 'Save networks button is disabled');
});

casper.then(function() {
    this.test.comment('Testing cluster networks: Save button interractions');
    var initialValue = this.evaluate(function(initialValue) {
            return __utils__.getFieldValue('management-cidr');
        });
    this.fill('.networks-table', {'management-cidr': '240.0.1.0/25'});
    this.evaluate(function() {
        $('input[name=management-cidr]').keyup();
    });
    this.test.assertExist('.apply-btn:not(:disabled)', 'Save networks button is enabled if there are changes');
    this.fill('.networks-table', {'management-cidr': initialValue});
    this.evaluate(function() {
        $('input[name=management-cidr]').keyup();
    });
    this.test.assertExists('.apply-btn:disabled', 'Save networks button is disabled again if there are no changes');
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
    this.test.comment('Testing cluster networks: data validation');
    var initialValue = this.evaluate(function(initialValue) {
            return __utils__.getFieldValue('management-cidr');
        });
    this.fill('.networks-table', {'management-cidr': '240.0.1.0/245'});
    this.evaluate(function() {
        $('input[name=management-cidr]').keyup();
    });
    this.test.assertExists('input[name=management-cidr].error', 'Field validation has worked');
    this.test.assertExists('.apply-btn:disabled', 'Save networks button is disabled if there is validation error');
    this.fill('.networks-table', {'management-cidr': initialValue});
    this.evaluate(function() {
        $('input[name=management-cidr]').keyup();
    });
    this.test.assertDoesntExist('input[name=management-cidr].error', 'Field validation works properly');
});

casper.then(function() {
    this.test.comment('Check Amount field validation');
    this.click('.net-manager input[type=radio]:not(:checked)');
    this.test.assertExists('.net-manager input[value=VlanManager]:checked', 'VLAN manager is chosen');
    var initialAmountValue = this.evaluate(function(initialValue) {
        return __utils__.getFieldValue('fixed-amount');
    });
    var initialVlanIDValue = this.evaluate(function(initialValue) {
        return __utils__.getFieldValue('fixed-vlan_range-start');
    });

    var fixtures = [
        {
            'amount': ' ',
            'vlanStart': '',
            'vlanEnd':'',
            'validationMessage': 'with empty field'
        },
        {
            'amount': '-10',
            'vlanStart': '',
            'vlanEnd':'',
            'validationMessage': 'when use negative number'
        },
        {
            'amount': '0',
            'vlanStart': '',
            'vlanEnd':'',
            'validationMessage': 'when use 0'
        },
        {
            'amount': '2',
            'vlanStart': '4094',
            'vlanEnd':'',
            'validationMessage': 'if amount more than 4095 - VLAN ID'
        },

        {
            'amount': '2',
            'vlanStart': '4093',
            'vlanEnd':'4094',
            'validationMessage': ''
        },
        {
            'amount': '4094',
            'vlanStart': '1',
            'vlanEnd':'4094',
            'validationMessage': ''
        },
        {
            'amount': '10',
            'vlanStart': '250',
            'vlanEnd':'259',
            'validationMessage': ''
        }

    ];

    this.each(fixtures, function(self, fixture) {
        self.then(function() {
            this.fill('.networks-table', {'fixed-amount': fixture.amount});
            if (fixture.vlanStart != '') {
                this.fill('.networks-table', {'fixed-vlan_range-start': fixture.vlanStart});
            }
            this.evaluate(function() {
                $('input[name=fixed-amount]').keyup();
            });
            if (fixture.vlanEnd == '') {
                this.test.assertExists('input[name=fixed-amount].error', 'Field validation has worked ' + fixture.validationMessage);
                this.test.assertExists('.apply-btn:disabled', 'Apply button is disabled if there is validation error');
            } else {
                this.test.assertEvalEquals(function() {return $('input[name=fixed-vlan_range-end]').val()}, fixture.vlanEnd, 'End value is correct');
                this.test.assertDoesntExist('input[name=fixed-amount].error', 'Field validation works properly with correct value');}
        });
    });

    casper.then(function() {
	this.fill('.networks-table', {
            'fixed-amount': '1',
            'fixed-vlan_range-start': '4094'
        });
        this.evaluate(function() {
            $('input[name=fixed-amount]').keyup();
        });
        this.test.assertDoesntExist('input[name=fixed-amount].error', 'Field validation works properly');
        this.test.assertDoesntExist('.networks-table.fixed-vlan-end', 'Field end vlan value works properly');
    });

    casper.then(function() {
        this.fill('.networks-table', {
            'fixed-amount': initialAmountValue,
            'fixed-vlan_range-start': initialVlanIDValue
        });
        this.click('.net-manager input[type=radio]:not(:checked)');
    });

});

casper.then(function() {
    this.test.comment('Check CIDR field validation');
    var initialCIDRValue = this.evaluate(function(initialValue) {
        return __utils__.getFieldValue('management-cidr');
    });

    var fixtures = [
        {
            'cidr': ' ',
            'validationMessage': 'empty field'
        },
        {
            'cidr': '0.10.-1.255/15',
            'validationMessage': 'negative number -1'
        },
        {
            'cidr': '0.-100.240.255/15',
            'validationMessage': 'negative number -100'
        },
        {
            'cidr': '0.256.240.255/15',
            'validationMessage': 'number out of area 255'
        },

        {
            'cidr': '0.750.240.255/15',
            'validationMessage': 'number 750'
        },
        {
            'cidr': '0.01.240.255/15',
            'validationMessage': 'number starts with 0'
        },
        {
            'cidr': '0.000.240.255/15',
            'validationMessage': 'number 000'
        },
        {
            'cidr': '0.50.240.255.45/15',
            'validationMessage': 'big amount of decimals groups'
        },
        {
            'cidr': '0.240.255/15',
            'validationMessage': 'little amount of decimals groups'
        },
        {
            'cidr': '0.1000.240.255/15',
            'validationMessage': 'bigger number of symbols in group'
        },
        {
            'cidr': '0..240.255/15',
            'validationMessage': 'any empty group'
        }

    ];

    this.each(fixtures, function(self, fixture) {
        self.then(function() {
            this.fill('.networks-table', {'management-cidr': fixture.cidr});
            this.evaluate(function() {
                $('input[name=management-cidr]').keyup();
            });
            this.test.assertExists('input[name=management-cidr].error', 'Field validation has worked properly in case of ' + fixture.validationMessage);
        });
    });


    casper.then(function() {
	this.fill('.networks-table', {'management-cidr': '0.10.100.255/15'});
        this.evaluate(function() {
            $('input[name=management-cidr]').keyup();
        });
        this.test.assertDoesntExist('input[name=management-cidr].error', 'Validation error description disappears if there are no errors');
    });

    casper.then(function() {
	this.fill('.networks-table', {'management-cidr': initialCIDRValue});
        this.evaluate(function() {
            $('input[name=management-cidr]').keyup();
        });
    });

});

casper.then(function() {
    this.test.comment('Check CIDR prefix');
    var initialCIDRValue = this.evaluate(function(initialValue) {
        return __utils__.getFieldValue('management-cidr');
    });

    function testCIDRprefix (fixtures, negativeTests) {
        casper.each(fixtures, function(self, fixture) {
            self.then(function() {
                this.fill('.networks-table', {'management-cidr': '240.0.1.0/' + fixture});
                this.evaluate(function() {
                    $('input[name=management-cidr]').keyup();
                });
                if (negativeTests) {
                    this.test.assertExists('input[name=management-cidr].error', 'Field validation has worked properly in case of prefix ' + fixture);
                } else {
                    this.test.assertDoesntExist('input[name=management-cidr].error', 'Field validation works properly in case of no errors (prefix ' + fixture +')');
                }
            });
        });
    }
    testCIDRprefix (['1', '-10', '0', '31', '75', 'test'], true);
    testCIDRprefix (['2', '30', '15'], false);

    casper.then(function() {
	this.fill('.networks-table', {'management-cidr': initialCIDRValue});
        this.evaluate(function() {
            $('input[name=management-cidr]').keyup();
        });
    });
});

casper.then(function() {
    this.test.comment('Check VlanID field validation');
    var initialVlanIDValue = this.evaluate(function(initialValue) {
        return __utils__.getFieldValue('public-vlan_start');
    });

    function testVlanID (fixtures, negativeTests) {
        casper.each(fixtures, function(self, fixture) {
            self.then(function() {
                this.fill('.networks-table', {'public-vlan_start': fixture});
                this.evaluate(function() {
                    $('input[name=public-vlan_start]').keyup();
                });
                if (negativeTests) {
                    this.test.assertExists('input[name=public-vlan_start].error', 'Field validation has worked properly in case of ' + fixture + ' value');
                } else {
                    this.test.assertDoesntExist('input[name=public-vlan_start].error', 'No validation errors in case of ' + fixture + ' value');
                }
            });
        });
    }
    testVlanID (['0', '4095', '-100', '5000'], true);
    testVlanID (['1', '4094', '2000'], false);

    casper.then(function() {
        this.fill('.networks-table', {'public-vlan_start': initialVlanIDValue});
        this.evaluate(function() {
            $('input[name=public-vlan_start]').keyup();
        });
    });
});

casper.then(function() {
    this.test.comment('Testing cluster networks: save changes');
    this.fill('.networks-table', {'management-cidr': '240.0.1.0/23'});
    this.evaluate(function() {
        $('input[name=management-cidr]').keyup();
    });
    this.click('.apply-btn:not(:disabled)');
    this.test.assertSelectorAppears('input:not(:disabled)');
    this.then(function() {
        this.test.assertDoesntExist('.alert-error', 'Correct settings were saved successfully');
    });
});

casper.then(function() {
    this.test.comment('Testing cluster networks: verification');
    this.click('.verify-networks-btn:not(:disabled)');
    this.test.assertSelectorAppears('.connect-3-error',
        'There should be atleast 1 node for dhcp check. And 2 nodes for connectivity check', 10000);

});

casper.then(function() {
    this.test.comment('Testing cluster networks: verification task deletion');
    this.fill('.networks-table', {'management-cidr': '240.0.1.0/22'});
    this.evaluate(function() {
        $('input[name=management-cidr]').keyup();
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
