include puppet-network

class nailytest::network_setup {

# $network_data example :
# $network_date = '[{"name":"eth0","vlan":"100","ip":"1.1.1.1","mask":"255.255.255.0","bcst":"1.1.1.255"},{...}]'

    class puppet-network {
        $arr = json2array($network_data)
        define iterator {
            network_config { "${name[intf]}.${name[vlan]}": ensure => present, bootproto => "static", vlan => "yes", ipaddr => $name[ip], netmask => $name[mask], broadcast => $name[bcst] }
        }

    network_config { "lo": }
    network_config { "eth0": bootproto => "dhcp", ensure => present }
    iterator { $arr: }

    }
}

