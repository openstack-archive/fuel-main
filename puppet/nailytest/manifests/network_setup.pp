class nailytest::network_setup {

include puppet-network
        define iterator($gateway,$dev,$vlan,$ip,$brd,$mask) {
            network_config { "$dev.$vlan": ensure => present, bootproto => "static", vlan => "yes", ipaddr => $ip, netmask => $mask, broadcast => $brd }
        }
        network_config { "lo": }
        network_config { "eth0": bootproto => "dhcp", ensure => present }
        create_resources(nailytest::network_setup::iterator,parsejson($network_data))
}

