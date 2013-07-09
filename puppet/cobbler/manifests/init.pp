#
# This class is intended to serve as
# a way of deploying cobbler server.
#
# [server] IP address that will be used as address of cobbler server.
# It is needed to download kickstart files, call cobbler API and
# so on. Required.
#
# [domain_name] Domain name that will be used as default for
# installed nodes. Required.
# [name_server] DNS ip address to be used by installed nodes
# [next_server] IP address that will be used as PXE tftp server. Required.
#
# [dhcp_start_address] First address of dhcp range
# [dhcp_end_address] Last address of dhcp range
# [dhcp_netmask] Netmask of the network
# [dhcp_gateway] Gateway address for installed nodes
# [dhcp_interface] Interface where to bind dhcp and tftp services
#
# [cobbler_user] Cobbler web interface username
# [cobbler_password] Cobbler web interface password
#
# [pxetimeout] Pxelinux will wail this count of 1/10 seconds before
# use default pxe item. To disable it use 0. Required.

class cobbler(

  $server             = $ipaddress,

  $domain_name        = 'local',
  $name_server        = $ipaddress,
  $next_server        = $ipaddress,

  $dhcp_start_address = '10.0.0.201',
  $dhcp_end_address   = '10.0.0.254',
  $dhcp_netmask       = '255.255.255.0',
  $dhcp_gateway       = $ipaddress,
  $dhcp_interface     = 'eth0',

  $cobbler_user       = 'cobbler',
  $cobbler_password   = 'cobbler',

  $pxetimeout         = '0'

  ){

  anchor { "cobbler-begin": }
  anchor { "cobbler-end": }

  Anchor<| title == "cobbler-begin" |> ->
  Class["cobbler::packages"] ->
  Class["cobbler::selinux"] ->
  Class["cobbler::iptables"] ->
  Class["cobbler::snippets"] ->
  Class["cobbler::server"] ->
  Anchor<| title == "cobbler-end" |>

  class { cobbler::packages : }
  class { cobbler::selinux : }
  class { cobbler::iptables : }
  class { cobbler::snippets : }
  class { cobbler::server : }

  cobbler_digest_user {$cobbler_user:
    password => $cobbler_password,
    require => Package[$cobbler::packages::cobbler_package],
    notify => Service[$cobbler::server::cobbler_service],
  }

}
