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
casper.then(function() {
    this.test.comment('Testing cluster page');
    this.test.assertExists('.summary .change-cluster-mode-btn:not(.disabled)', 'Cluster deployment mode is changeable');
    this.test.assertExists('.summary .change-cluster-type-btn:not(.disabled)', 'Cluster type is changeable');
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
        this.test.assertExists('.modal input[type=radio][name=mode][value=simple]:checked', 'Simple deployment mode chosen');
        this.click('.modal input[type=radio][name=mode][value=ha]');
        this.test.assertVisible('.modal input[name=redundancy]', 'Cluster redundancy input is visible if deployment mode is HA');
        this.click('.modal .apply-btn');
    });
    this.test.assertSelectorDisappears('.modal', 'Cluster deployment mode dialog closes after setting deployment mode to HA');
    this.then(function() {
        this.click('.summary .change-cluster-mode-btn');
    });
    this.test.assertSelectorAppears('.modal', 'Cluster deployment mode dialog opens again');
    this.then(function() {
        this.test.assertExists('.modal input[type=radio][name=mode][value=ha]:checked', 'HA deployment mode chosen');
        this.click('.modal input[type=radio][name=mode][value=simple]');
        this.test.assertNotVisible('.modal input[name=redundancy]', 'Cluster redundancy input is not visible if deployment mode is simple');
        this.click('.modal .apply-btn');
    });
    this.test.assertSelectorDisappears('.modal', 'Cluster deployment mode dialog closes after setting deployment mode to simple');
});

casper.then(function() {
    this.test.comment('Testing cluster type dialog');
    this.click('.summary .change-cluster-type-btn');
    this.test.assertSelectorAppears('.modal', 'Cluster type dialog opens');
    this.then(function() {
        this.test.assertExists('.modal input[type=radio][name=type][value=both]:checked', 'Compute and storage type chosen');
        this.click('.modal input[type=radio][name=type][value=compute]');
        this.click('.modal .apply-btn');
    });
    this.test.assertSelectorDisappears('.modal', 'Cluster type dialog closes after setting type to Compute only');
    this.then(function() {
        this.test.assertEvalEquals(function() {return $('.node-list').length}, 2, 'Number of available roles after type change is correct');
    });
});

casper.then(function() {
    this.test.comment('Testing node addition to controller role');
    this.click('.node-list-controller .btn-add-nodes');
    this.waitForSelector('.add-nodes-screen');
    this.waitWhileSelector('.add-nodes-screen .available-nodes .progress');
    this.then(function() {
        this.test.assertEvalEquals(function() {return $('.add-nodes-screen .nodebox').length}, nodes.length, 'Number of unallocated nodes is correct');
        this.evaluate(function() {
            $('.add-nodes-screen .nodebox').click(); // clicks all available nodes, this.click clicks only one
        });
        this.test.assertEvalEquals(function() {return $('.add-nodes-screen .nodebox.node-to-add-checked').length}, 1, 'Only one node is checkable for controller role in Simple deployment mode');
        this.click('.add-nodes-screen .btn-apply');
    });
    this.waitForSelector('.nodes-by-roles-screen');
    this.waitFor(function() {
        return this.evaluate(function() {
            return $('.node-list-controller .nodebox:not(.nodeplaceholder)').length == 1;
        });
    }, function() {
        this.test.pass('Scheduled for addition controller appears in node list');
    });
    this.then(function() {
        this.test.assertDoesntExist('.node-list-controller .nodebox.nodeplaceholder', 'Placeholder for controller node disappears');
    });
});

casper.then(function() {
    this.test.comment('Testing node addition to compute role');
    this.click('.node-list-compute .btn-add-nodes');
    this.waitForSelector('.add-nodes-screen');
    this.waitWhileSelector('.add-nodes-screen .available-nodes .progress');
    this.then(function() {
        this.evaluate(function() {
            $('.add-nodes-screen .nodebox').click();
        });
        this.test.assertEvalEquals(function() {return $('.add-nodes-screen .nodebox.node-to-add-checked').length}, nodes.length - 1, 'All nodes are checkable for compute role');
        this.click('.add-nodes-screen .btn-apply');
    });
    this.waitForSelector('.nodes-by-roles-screen');
    this.waitFor(function() {
        return (nodes.length - 1) == this.evaluate(function() {
            return $('.node-list-compute .nodebox').length;
        });
    }, function() {
        this.test.pass('Scheduled for addition computes appear in node list');
    });
});

casper.then(function() {
    this.test.comment('Testing deletion of compute node, scheduled for addition');
    this.click('.node-list-compute .btn-delete-nodes');
    this.waitForSelector('.delete-nodes-screen');
    this.then(function() {
        this.evaluate(function() {
            $('.delete-nodes-screen .nodebox:first').click();
        });
        this.click('.delete-nodes-screen .btn-apply');
    });
    this.waitForSelector('.nodes-by-roles-screen');
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
        this.test.assertExists('.summary .change-cluster-type-btn.disabled', 'Cluster type is not changeable');
        this.test.assertDoesntExist('.node-list .btn-add-nodes:not(.disabled)', 'All Add Node buttons are disabled');
        this.test.assertDoesntExist('.node-list .btn-delete-nodes:not(.disabled)', 'All Delete Node buttons are disabled');
        this.test.info('Waiting for deployment readiness...');
    });
    this.test.assertSelectorDisappears('.deployment-control .progress', 'Deployment progress bar disappears', 10000);
    this.then(function() {
        this.test.assertExists('.summary .change-cluster-type-btn:not(.disabled)', 'Cluster type is changeable again');
        this.test.assertExists('.node-list .btn-add-nodes:not(.disabled)', 'Add Node buttons are enabled again');
        this.test.assertExists('.node-list .btn-delete-nodes:not(.disabled)', 'Delete Node buttons are enabled again');
        this.test.assertSelectorHasText('.task-result', 'Success', 'Message about successful deployment appeared');
    });
});

casper.run(function() {
    this.test.done();
});
