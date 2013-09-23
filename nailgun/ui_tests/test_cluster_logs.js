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
casper.createNode({status: 'ready', mac: '84:AA:B8:E6:30:F0', cluster_id: 1});
casper.loadPage('#cluster/1/logs').waitForSelector('#tab-logs > *');
casper.then(function() {
    if (this.loadJsFile('sinon-server')) {
        this.evaluate(function() {
            var server = sinon.fakeServer.create();
            server.autoRespond = true;
            server.respondWith(/\/api\/logs.*/, [
                200, {"Content-Type": "application/json"},
                JSON.stringify({
                    from: 1,
                    entries: [['Date', 'INFO', 'Test Log Entry']]
                })
            ]);
        });
    } else {
        this.test.error('Unable to load sinon');
        this.test.done();
    }
});

casper.then(function() {
    this.test.comment('Testing logs tab');
    this.test.assertSelectorAppears('.filter-bar select[name=node] option', 'Node selection box appears and is not empty');
    this.test.assertSelectorAppears('.filter-bar select[name=source] option', 'Log source selection box appears and is not empty');
    this.test.assertSelectorAppears('.filter-bar .show-logs-btn:not([disabled])', '"Show logs" button is available');
    this.then(function() {
        this.click('.filter-bar .show-logs-btn');
    });
    this.waitForSelector('.table-logs .log-entries > *').then(function() {
        this.test.assertSelectorHasText('.table-logs .log-entries tr:first-child td:last-child', 'Test Log Entry', 'Log entry appears after clicking "Show logs" button');
    });
});

casper.run(function() {
    this.test.done();
});
