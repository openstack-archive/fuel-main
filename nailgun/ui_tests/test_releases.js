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
casper.start().loadPage('#releases');

casper.then(function() {
    this.test.comment('Testing releases page layout');
    this.test.assertEvalEquals(function() {return $('.releases-table tbody tr').length}, 2, 'There are two releases presented');
    this.test.assertSelectorAppears('.releases-table .not_available', 'There is unavailable release');
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
        this.click('.modal input[type=radio]:not(:checked)');
        this.fill('.modal form.rhel-license', {'username': 'rheltest', 'password': 'password'});
        this.click('.modal .btn-os-download');
    });
    this.test.assertSelectorDisappears('.modal', 'RHEL credentials popup was closed');
    this.test.assertSelectorAppears('.progress', 'RHEL downloading started');
    this.test.assertSelectorDisappears('.progress', 'RHEL downloading finished');
    this.then(function() {
        this.test.assertDoesntExist('.releases-table .not_available', 'All releases are available');
    });
});

casper.run(function() {
    this.test.done();
});
