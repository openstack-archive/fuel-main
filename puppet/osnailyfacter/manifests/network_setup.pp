define setup_interfaces (
  $interface = $name,
  $network_settings
) {
  $ipaddr = $network_settings[$interface]['ipaddr']
  $gateway = $network_settings[$interface]['gateway']
  notify{"${interface} => ${ipaddr}, ${gateway}":}
  l23network::l3::ifconfig{$interface:
    ipaddr        => $ipaddr,
    gateway       => $gateway,
    check_by_ping => 'none'
  }
}

define check_base_interfaces (
  $interface = $name,
) {
  $b_iface = split($interface, '.')
  if size($b_iface) > 1 {
    if ! defined(L23network::L3::Ifconfig[$b_iface]) {
      l23network::l3::ifconfig{$b_iface:
        ipaddr        => 'none',
      }
    }
    L23network::L3::Ifconfig<| title == $b_iface |> ->
    L23network::L3::Ifconfig<| title == $interface |>
  }
}

class osnailyfacter::network_setup (
  interfaces = keys(parsejson($network_data)),
  network_settings = parsejson($network_data),
) {
  setup_interfaces{$interfaces: network_settings=>$network_settings} ->
  check_base_interfaces{$interfaces:}
}
