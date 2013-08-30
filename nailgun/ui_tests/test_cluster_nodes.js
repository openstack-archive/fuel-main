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
var nodes = [
    {status: 'discover', manufacturer: 'Dell', mac: 'C0:8D:DF:52:76:F1'},
    {status: 'discover', manufacturer: 'HP', mac: '46:FC:5A:0C:F9:51'},
    {status: 'discover', manufacturer: 'Supermicro', mac: '84:AA:B8:E6:30:F0'}
];
nodes.forEach(function(node) {
    casper.createNode(node);
})
casper.loadPage('#cluster/1/nodes').waitForSelector('#tab-nodes > *');
/*
 * Nodes page is being overhauled, disable all related tests for now

casper.then(function() {
    this.test.comment('Testing cluster page');
    this.test.assertExists('.summary .change-cluster-mode-btn:not(.disabled)', 'Cluster deployment mode is changeable');
    this.test.assertDoesntExist('.node-list .btn-add-nodes.disabled', 'All Add Node buttons are enabled');
    this.test.assertDoesntExist('.node-list .btn-delete-nodes:not(.disabled)', 'All Delete Node buttons are disabled');
    this.test.assertExists('.node-list-controller .nodebox.nodeplaceholder', 'Placeholder for controller node presents');
    this.test.assertEvalEquals(function() {return $('.node-list').length}, 3, 'Number of available roles is correct');
});

casper.then(function() {
    this.test.comment('Testing cluster deployment mode dialog');
    this.click('.summary .change-cluster-mode-btn');
    this.test.assertSelectorAppears('.modal', 'Cluster deployment mode dialog opens');
    this.then(function() {
        this.test.assertExists('.modal input[type=radio][name=mode][value=multinode]:checked', 'Multinode deployment mode chosen');
        this.click('.modal input[type=radio][name=mode][value=ha]');
        this.click('.modal .apply-btn');
    });
    this.test.assertSelectorDisappears('.modal', 'Cluster deployment mode dialog closes after setting deployment mode to Multi-node with HA');
    this.then(function() {
        this.test.assertEvalEquals(function() {return $('.node-list').length}, 3, 'Number of available roles after mode change is correct');
        this.click('.summary .change-cluster-mode-btn');
    });
    this.test.assertSelectorAppears('.modal', 'Cluster deployment mode dialog opens again');
    this.then(function() {
        this.test.assertExists('.modal input[type=radio][name=mode][value=ha]:checked', 'Multi-node with HA deployment mode chosen');
        this.click('.modal input[type=radio][name=mode][value=multinode]');
        this.click('.modal .apply-btn');
    });
    this.test.assertSelectorDisappears('.modal', 'Cluster deployment mode dialog closes after setting deployment mode to Multi-node');
});

casper.then(function() {
    this.test.comment('Testing node addition to controller role');
    this.click('.node-list-controller .btn-add-nodes');
    this.test.assertSelectorAppears('.add-nodes-screen', 'Add controller nodes screen appears');
    this.test.assertSelectorDisappears('.add-nodes-screen .available-nodes .progress', 'Available for addition controllers are loaded');
    this.then(function() {
        this.test.assertEvalEquals(function() {return $('.add-nodes-screen .nodebox').length}, nodes.length, 'Number of unallocated nodes is correct');
        this.evaluate(function() {
            $('.add-nodes-screen .nodebox').click(); // clicks all available nodes, this.click clicks only one
        });
        this.test.assertEvalEquals(function() {return $('.add-nodes-screen .nodebox.node-to-add-checked').length}, 1, 'Only one node is checkable for controller role in Simple deployment mode');
        this.click('.add-nodes-screen .btn-apply');
    });
    this.test.assertSelectorAppears('.nodes-by-roles-screen', 'Return to nodes tab');
    this.test.assertSelectorAppears('.node-list-controller .nodebox:not(.nodeplaceholder)', 'Scheduled for addition controller appears in node list');
    this.then(function() {
        this.test.assertDoesntExist('.node-list-controller .nodebox.nodeplaceholder', 'Placeholder for controller node disappears');
    });
});

casper.then(function() {
    this.test.comment('Testing node addition to compute role');
    this.click('.node-list-compute .btn-add-nodes');
    this.test.assertSelectorAppears('.add-nodes-screen', 'Add compute nodes screen appears');
    this.test.assertSelectorDisappears('.add-nodes-screen .available-nodes .progress', 'Available for addition computes are loaded');
    this.then(function() {
        this.evaluate(function() {
            $('.add-nodes-screen .nodebox').click();
        });
        this.test.assertEvalEquals(function() {return $('.add-nodes-screen .nodebox.node-to-add-checked').length}, nodes.length - 1, 'All nodes are checkable for compute role');
        this.click('.add-nodes-screen .btn-apply');
    });
    this.test.assertSelectorAppears('.nodes-by-roles-screen', 'Return to nodes tab');
    this.test.assertSelectorAppears('.node-list-compute .nodebox', 'Scheduled for addition computes appear in node list');
});

casper.then(function() {
    this.test.comment('Testing deletion of compute node, scheduled for addition');
    this.click('.node-list-compute .btn-delete-nodes');
    this.test.assertSelectorAppears('.delete-nodes-screen', 'Delete compute nodes screen appears');
    this.then(function() {
        this.click('.delete-nodes-screen .nodebox');
        this.click('.delete-nodes-screen .btn-apply');
    });
    this.test.assertSelectorAppears('.nodes-by-roles-screen', 'Return to nodes tab');
    this.waitFor(function() {
        return (nodes.length - 2) == this.evaluate(function() {
            return $('.node-list-compute .nodebox').length;
        });
    }, function() {
        this.test.pass('Deleted node disappears from node list');
    });
});

casper.then(function() {
    this.test.comment('Testing deployment');
    this.click('.deployment-control .deploy-btn');
    this.test.assertSelectorAppears('.modal', 'Deployment dialog opens');
    this.then(function() {
        this.click('.modal .start-deployment-btn');
    });
    this.test.assertSelectorDisappears('.modal', 'Deployment dialog closes after clicking Start Deployment');
    this.test.assertSelectorAppears('.deployment-control .progress', 'Deployment progress bar appears');
    this.then(function() {
        this.test.assertDoesntExist('.node-list .btn-add-nodes:not(.disabled)', 'All Add Node buttons are disabled');
        this.test.assertDoesntExist('.node-list .btn-delete-nodes:not(.disabled)', 'All Delete Node buttons are disabled');
        this.test.info('Waiting for deployment readiness...');
    });
    this.test.assertSelectorDisappears('.deployment-control .progress', 'Deployment progress bar disappears', 60000);
    this.then(function() {
        this.test.assertDoesntExist('.summary .change-cluster-mode-btn:not(.disabled)', 'Cluster mode is not changeable');
        this.test.assertExists('.node-list .btn-add-nodes:not(.disabled)', 'Add Node buttons are enabled again');
        this.test.assertExists('.node-list .btn-delete-nodes:not(.disabled)', 'Delete Node buttons are enabled again');
        this.test.assertSelectorHasText('.task-result', 'Success', 'Message about successful deployment appeared');
    });
});
*/

casper.run(function() {
    this.test.done();
});
