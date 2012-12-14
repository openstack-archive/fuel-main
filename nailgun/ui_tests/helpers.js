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
    options.meta = {
        "block_device": {
            "ram0": {
                "removable": "0",
                "size": "1228800"
            },
            "sda": {
                "vendor": "ATA",
                "removable": "0",
                "rev": "0.14",
                "state": "running",
                "timeout": "30",
                "model": "QEMU HARDDISK",
                "size": "16777216"
            }
        },
        "interfaces": [
            {
                "addresses": {
                    "fe80::5054:ff:fe28:16c3": {
                        "prefixlen": "64",
                        "scope": "Link",
                        "family": "inet6"
                    },
                    "52:54:00:28:16:C3": {
                        "family": "lladdr"
                    },
                    "10.20.0.229": {
                        "prefixlen": "24",
                        "scope": "Global",
                        "netmask": "255.255.255.0",
                        "broadcast": "10.20.0.255",
                        "family": "inet"
                    }
                },
                "name": "eth0"
            },
            {
                "default_interface": "eth0"
            },
            {
                "default_gateway": "10.20.0.2"
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
            "anon_pages": "16420kB",
            "vmalloc_total": "34359738367kB",
            "bounce": "0kB",
            "active": "28576kB",
            "inactive": "20460kB",
            "nfs_unstable": "0kB",
            "vmalloc_used": "7160kB",
            "total": "1019548kB",
            "slab": "16260kB",
            "buffers": "4888kB",
            "slab_unreclaim": "7180kB",
            "swap": {
                "cached": "0kB",
                "total": "0kB",
                "free": "0kB"
            },
            "dirty": "84kB",
            "writeback": "0kB",
            "vmalloc_chunk": "34359729156kB",
            "free": "322008kB",
            "page_tables": "1328kB",
            "cached": "27728kB",
            "commit_limit": "509772kB",
            "committed_as": "54864kB",
            "mapped": "5380kB",
            "slab_reclaimable": "9080kB"
        },
        "serial": "Unknown",
        "networks": {
            "floating": {
                "access": "public",
                "device": "eth0",
                "netmask": "255.255.255.0",
                "vlan_id": 300,
                "address": "172.18.0.2"
            },
            "management": {
                "access": "private172",
                "device": "eth0",
                "netmask": "255.255.255.0",
                "vlan_id": 100,
                "address": "10.0.0.2"
            },
            "storage": {
                "access": "private192",
                "device": "eth0",
                "netmask": "255.255.255.0",
                "vlan_id": 200,
                "address": "10.0.1.2"
            }
        }
    };
    return this.thenOpen(baseUrl + 'api/nodes', {
        method: 'post',
        headers: {'Content-Type': 'application/json'},
        data: JSON.stringify(options)
    });
}
