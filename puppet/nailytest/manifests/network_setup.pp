include puppet-network

class nailytest::network_setup {

    class puppet-network {
        $arr = json2array($interfaces)
        define iterator {
            network_config { "${name[intf]}.${name[vlan]}": ensure => present, bootproto => "static", vlan => "yes", ipaddr => $name[ip], netmask => $name[mask], broadcast => $name[bcst] }
        }

    network_config { "lo": }
    network_config { "eth0": bootproto => "dhcp", ensure => present }
    network_config { "eth1": bootproto => "dhcp", ensure => present }
    iterator { $arr: }

    }
}





