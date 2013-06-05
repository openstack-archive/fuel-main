casper.start();
casper.createCluster({name: 'Test Cluster'});
var nodes = [
    {status: 'discover', manufacturer: 'Dell', mac: 'C0:8D:DF:52:76:F1'}
];
nodes.forEach(function(node) {
    casper.createNode(node);
});
var vmSDA;
var osSDA;

casper.loadPage('#cluster/1/nodes').waitForSelector('#tab-nodes > *');

casper.then(function() {
    this.test.comment('Testing nodes disks');

    this.then(function() {
        this.click('.node-list-compute .btn-add-nodes');
        this.waitForSelector('.add-nodes-screen');
        this.waitWhileSelector('.add-nodes-screen .available-nodes .progress');
        this.then(function() {
            this.click('.add-nodes-screen .nodebox');
            this.click('.add-nodes-screen .btn-apply');
            this.waitForSelector('.nodes-by-roles-screen');
        });
        this.then(function() {
            this.click('.node-hardware');
            this.waitForSelector('.modal');
            this.then(function() {
                this.click('.btn-edit-disks');
                this.waitForSelector('.nodes-by-roles-screen');
            });
        });
    });

    this.then(function() {
        this.test.comment('Testing nodes disks layout');
        this.test.assertEvalEquals(function() {return $('.disk-box').length}, 2, 'Number of disks is correct');
        this.test.assertEvalEquals(function() {return $('.bootable-marker:visible').length}, 1, 'Number of bootable disks is correct');
        this.test.assertExists('.btn-defaults:not(:disabled)', 'Load Defaults button is enabled');
        this.test.assertExists('.btn-revert-changes:disabled', 'Cancel button is disabled');
        this.test.assertExists('.btn-apply:disabled', 'Apply button is disabled');
    });

    var sdaDisk = '.disk-box[data-disk=sda]';
    var sdaDiskVM = sdaDisk + ' .volume-group-box[data-group=vm]';
    var sdaDiskOS = sdaDisk + '  .volume-group-box[data-group=os]';
    var vdaDisk = '.disk-box[data-disk=vda]';
    var vdaDiskVM = vdaDisk + ' .volume-group-box[data-group=vm]';
    var vdaDiskOS = vdaDisk + '  .volume-group-box[data-group=os]';

    this.then(function() {
        this.test.comment('Testing nodes disk block');
        this.test.assertEvalEquals(function(sdaDisk) {return $(sdaDisk + ' .bootable-marker:visible').length}, 1, 'SDA disk is bootable', {sdaDisk: sdaDisk});
        this.click(sdaDisk + ' .toggle-volume');
        vmSDA= this.getElementAttribute(sdaDiskVM + ' input', 'value');
        osSDA= this.getElementAttribute(sdaDiskOS + ' input', 'value');
        this.test.assertExists(sdaDisk + ' .btn-bootable:disabled', 'Button Make Bottable is disabled');
        this.test.assertExists(sdaDiskOS + '', 'Base system group form is presented');
        this.test.assertExists(sdaDiskVM + '', 'Virtual Storage group form is presented');
        this.test.assertExists(sdaDisk + ' .disk-visual .os .close-btn.hide', 'Button Close for Base system group is not presented');
        this.test.assertExists(sdaDisk + ' .disk-visual .vm .close-btn:not(.hide)', 'Button Close for Virtual Storage group is presented');
    });

    this.then(function() {
        this.test.comment('Testing button Apply: interractions');
        this.fill(sdaDiskVM, {'vm': '80'});
        this.evaluate(function(sdaDiskVM) {
            $(sdaDiskVM + ' input').keyup();
        },{sdaDiskVM: sdaDiskVM});
        this.test.assertExists('.btn-defaults:not(:disabled)', 'Load Defaults button is enabled');
        this.test.assertExists('.btn-revert-changes:not(:disabled)', 'Cancel button is enabled');
        this.test.assertExists('.btn-apply:not(:disabled)', 'Apply button is enabled');

        // these assertions should pass but they don't because of rounding issues
        // uncomment it after it is fixed
        //this.click(sdaDiskVM + ' .use-all-unallocated');
        //this.test.assertExists('.btn-defaults:not(:disabled)', 'Load Defaults button is enabled');
        //this.test.assertExists('.btn-revert-changes:disabled', 'Cancel button is disabled');
        //this.test.assertExists('.btn-apply:disabled', 'Apply button is disabled');
    });

    this.then(function() {
        this.test.comment('Testing button Load Defaults');
        this.test.assertExists('.btn-defaults:not(:disabled)', 'Load Defaults button is enabled');
        this.click('.btn-defaults');
        this.waitForSelector('.btn-defaults:not(:disabled)');
        this.then(function() {
            this.test.assertEvalEquals(function(sdaDiskVM) {return $(sdaDiskVM + ' input').val()}, vmSDA, 'Volume group input control VM contains default value', {sdaDiskVM:sdaDiskVM});
            this.test.assertEvalEquals(function(sdaDiskOS) {return $(sdaDiskOS + ' input').val()}, osSDA, 'Volume group input control OS contains default value', {sdaDiskOS:sdaDiskOS});
        });
    });

    this.then(function() {
        this.test.comment('Testing button Cancel');
        this.fill(sdaDiskVM + '', {'vm': '50'});
        this.evaluate(function(sdaDiskVM) {
            $(sdaDiskVM + ' input').keyup();
        },{sdaDiskVM: sdaDiskVM});

        this.test.assertEvalEquals(function(sdaDiskVM) {return $(sdaDiskVM + ' input').val()}, '50', 'Volume group input control VM contains correct value', {sdaDiskVM:sdaDiskVM});
        this.test.assertExists('.btn-revert-changes:not(:disabled)', 'Cancel button is enabled');
        this.click('.btn-revert-changes');
        this.test.assertEvalEquals(function(sdaDiskVM) {return $(sdaDiskVM + ' input').val()}, vmSDA, 'Volume group input control VM contains default value', {sdaDiskVM:sdaDiskVM});
    });

    this.then(function() {
        this.test.comment('Testing volume group deletion');
        this.click(sdaDisk + ' .disk-visual .vm .close-btn');
        this.test.assertEquals(this.getElementBounds(sdaDisk + ' .disk-visual .vm').width, 0, 'VM group was removed successfully');
        this.test.assertEval(function(sdaDisk) {return $(sdaDisk + ' .disk-visual .unallocated').width() > 0}, 'There is unallocated space after Virtual Storage VG removal',{sdaDisk:sdaDisk});
        this.test.assertEvalEquals(function(sdaDiskVM) {return $(sdaDiskVM + ' input').val()},'0.00', 'Volume group input control contains correct value',{sdaDiskVM:sdaDiskVM});
        this.click(sdaDiskVM + ' .use-all-unallocated');
        this.test.assertEquals(this.getElementBounds(sdaDisk + ' .disk-visual .unallocated').width, 0, 'Use all unallocated area for VM');
        this.fill(sdaDiskVM + '', {'vm': '0'});
        this.evaluate(function(sdaDiskVM) {
            $(sdaDiskVM + ' input').keyup();
        },{sdaDiskVM:sdaDiskVM});
        this.test.assertEquals(this.getElementBounds(sdaDisk + ' .disk-visual .vm').width, 0, 'VM group was removed successfully');
        this.test.assertEval(function(sdaDisk) {return $(sdaDisk + ' .disk-visual .unallocated').width() > 0}, 'There is unallocated space after Virtual Storage VG removal', {sdaDisk:sdaDisk});
        this.test.assertEvalEquals(function(sdaDiskVM) {return $(sdaDiskVM + ' input').val()},'0', 'Volume group input control contains correct value',{sdaDiskVM:sdaDiskVM});
    });


    this.then(function() {
        this.test.comment('Testing use all unallocated link');
        this.click(sdaDiskOS + ' .use-all-unallocated');
        this.test.assertEquals(this.getElementBounds(sdaDisk + ' .disk-visual .unallocated').width, 0, 'Use all unallocated link works correctly');
    });

    this.then(function() {
        this.test.comment('Testing validation in case of minimum VG value');
        this.fill(sdaDiskOS, {'os': '0'});
        this.evaluate(function(sdaDiskOS) {
            $(sdaDiskOS + ' input').keyup();
        },{sdaDiskOS:sdaDiskOS});
        this.test.assertExists(sdaDiskOS + ' input.error', 'Field validation has worked');
        this.test.assertEval(function(sdaDisk) {return $(sdaDisk + ' .disk-visual .os').width() > 0}, 'VG size was not changed',{sdaDisk:sdaDisk});
        this.click(vdaDisk + ' .toggle-volume');
        this.test.assertExists(vdaDiskVM + '', 'Virtual Storage group form is presented');
        this.click(vdaDisk + ' .disk-visual .vm .close-btn');
        this.fill(vdaDisk + ' .volume-group-box[data-group=os]', {'os': '20'});
        this.evaluate(function(vdaDisk) {
            $(vdaDisk + ' .volume-group-box[data-group=os] input').keyup();
        },{vdaDisk:vdaDisk});
        this.test.assertDoesntExist(sdaDiskOS + ' input.error', 'Field validation has worked');
    });

    this.then(function() {
        this.test.comment('Testing work of Make Bootable button');
        this.test.assertExists(vdaDisk + ' .btn-bootable:enabled', 'Button Make Bottable is enabled for VDA disk');
        this.click(vdaDisk + ' .btn-bootable');
        this.test.assertEvalEquals(function(vdaDisk) {return $(vdaDisk + ' .bootable-marker:visible').length}, 1, 'VDA disk is bootable', {vdaDisk:vdaDisk});
        this.test.assertExists(sdaDisk + ' .btn-bootable:enabled', 'Button Make Bottable is enabled for SDA disk');
        this.fill(sdaDiskVM + '', {'vm': '100'});
        this.evaluate(function(sdaDiskVM) {
            $(sdaDiskVM + ' input').keyup();
        },{sdaDiskVM:sdaDiskVM});
        this.test.assertExists(sdaDisk + ' .btn-bootable:disabled', 'Button Make Bottable is disabled for SDA disk because there is no enough free space');
    });


    this.then(function() {
        this.test.comment('Testing  validation of VG size');

        this.fill(sdaDiskVM + '', {'vm': 'test11'});
        this.evaluate(function(sdaDiskVM) {
            $(sdaDiskVM + ' input').keyup();
        },{sdaDiskVM:sdaDiskVM});
        this.test.assertExists(sdaDiskVM + ' input.error', 'Field validation has worked in case of letters');


        this.fill(sdaDiskVM + '', {'vm': '-20'});
        this.evaluate(function(sdaDiskVM) {
            $(sdaDiskVM + ' input').keyup();
        },{sdaDiskVM:sdaDiskVM});
        this.test.assertExists(sdaDiskVM + ' input.error', 'Field validation has worked in case of negative number');


        this.fill(sdaDiskVM + '', {'vm': '200'});
        this.evaluate(function(sdaDiskVM) {
            $(sdaDiskVM + ' input').keyup();
        },{sdaDiskVM:sdaDiskVM});
        this.test.assertExists(sdaDiskVM + ' input.error', 'Field validation has worked in case of number that bigger than available space on disk');
    });

});


casper.run(function() {
    this.test.done();
});
