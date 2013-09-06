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
casper.start().loadPage('#clusters');

casper.then(function() {
    this.test.comment('Testing cluster list page');
    this.test.assertExists('.cluster-list', 'Cluster container exists');
    this.test.assertExists('.create-cluster', 'Cluster creation control exists');
});

casper.then(function() {
    this.test.comment('Testing cluster creation');
    var name = 'Test Cluster';
    this.click('.create-cluster');
    this.test.assertSelectorAppears('.modal', 'Cluster creation dialog opens');
    this.test.assertSelectorAppears('.modal form select[name=release] option', 'Release select box updates with releases');
    this.then(function() {
        this.evaluate(function() {
            $('form.create-cluster-form select[name=release]').val(2).trigger('change');
        });
        this.test.assertSelectorAppears('form.rhel-license', 'RHEL credentials form appears after selecting RHOS');
    });
    this.then(function() {
        this.fill('form.create-cluster-form', {name: name});
        this.fill('form.rhel-license', {username: 'rheltest', password: 'password'});
        for (var i = 0; i < 4; i++) {
            this.click('.next-pane-btn');
        }
        this.click('.finish-btn');
    });
    this.test.assertSelectorDisappears('.modal', 'Cluster creation dialog closes after from submission');
    this.test.assertSelectorAppears('.cluster-list a.clusterbox', 'Created cluster appears in list');
    this.then(function() {
        this.test.assertSelectorHasText('.cluster-list a.clusterbox .cluster-name', name, 'Created cluster has specified name');
    })
});

casper.run(function() {
    this.test.done();
});
