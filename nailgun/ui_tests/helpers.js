var baseUrl = 'http://127.0.0.1:5544/';

casper.loadPage = function(page) {
    return this.thenOpen(baseUrl + page).waitWhileSelector('#content > .loading');
}

casper.loadJsFile = function(file) {
    return this.page.injectJs('ui_tests/' + file + '.js');
}

casper.test.assertSelectorAppears = function(selector, message, timeout) {
    return this.casper.waitForSelector(selector, function () {
        this.test.pass(message);
    }, function() {
        this.test.fail(message);
    }, timeout);
}

casper.test.assertSelectorDisappears = function(selector, message, timeout) {
    return this.casper.waitWhileSelector(selector, function () {
        this.test.pass(message);
    }, function() {
        this.test.fail(message);
    }, timeout);
}

casper.createCluster = function(options) {
    options.release = 1;
    return this.thenOpen(baseUrl + 'api/clusters', {
        method: 'post',
        headers: {'Content-Type': 'application/json'},
        data: JSON.stringify(options)
    });
}

casper.createNode = function(options) {
    var mac = '52:54:00:96:81:6E';
    if('mac' in options) {
        mac = options['mac'];
    }

    options.meta = {
        "disks": [
            {
                "model": "TOSHIBA MK3259GS",
                "disk": "blablabla1",
                "name": "sda",
                "size": 100010485760
            },
            {
                "model": "TOSHIBA",
                "disk": "blablabla2",
                "name": "vda",
                "size": 80010485760
            }
        ],
        "interfaces": [
            {
              "mac": mac,
              "name": "eth0",
              "max_speed": 1000,
              "current_speed": 100
            },
            {
              "mac": "C8:0A:A9:A6:FF:28",
              "name": "eth1",
              "max_speed": 1000,
              "current_speed": 1000
            },
            {
              "mac": "D4:56:C3:88:99:DF",
              "name": "eth0:1",
              "max_speed": 2000,
              "current_speed": null
            }
        ],
        "cpu": {
            "real": 0,
            "0": {
                "family": "6",
                "vendor_id": "GenuineIntel",
                "mhz": "3192.766",
                "stepping": "3",
                "cache_size": "4096 KB",
                "flags": [
                    "fpu",
                    "lahf_lm"
                ],
                "model": "2",
                "model_name": "QEMU Virtual CPU version 0.14.1"
            },
            "total": 1
        },
        "memory": {
            "slots": 6,
            "total": 4294967296,
            "maximum_capacity": 8589934592,
            "devices": [
                {
                    "size": 1073741824
                },
                {
                    "size": 1073741824
                },
                {
                    "size": 1073741824
                },
                {
                    "size": 1073741824
                }
            ]
        }
    };
    return this.thenOpen(baseUrl + 'api/nodes', {
        method: 'post',
        headers: {'Content-Type': 'application/json'},
        data: JSON.stringify(options)
    });
}
