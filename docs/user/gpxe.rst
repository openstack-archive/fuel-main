GPXE
====

If you try to use virtual machines to launch **FuelWeb** then you have to be sure that dnsmasq on master node is configured to support that PXE client you use on your virtual machines. We enabled *dhcp-no-override* option because without it enabled dnsmasq tries to move out PXE filename and PXE servername special fields into DHCP options. Not all PXE implementations can understand those options and therefore they will not be able to boot. For example, Centos 6.3 uses gPXE implementation instead of more advanced iPXE by default.
