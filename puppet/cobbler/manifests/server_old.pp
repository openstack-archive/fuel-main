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

class cobbler::server(
  $server             = $ipaddress,

  $domain_name        = 'example.com',
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
  ) {

  Exec {path => '/usr/bin:/bin:/usr/sbin:/sbin'}

  case $operatingsystem {
    /(?i)(centos|redhat)/:  {
      $cobbler_package = "cobbler"
      $cobbler_web_package = "cobbler-web"
      $dnsmasq_package = "dnsmasq"
      $cobbler_service = "cobblerd"
      $cobbler_web_service = "httpd"
      $cobbler_additional_packages = ["xinetd", "tftp-server", "syslinux", "wget"]
    }
    /(?i)(debian|ubuntu)/:  {
      $cobbler_package = "cobbler"
      $cobbler_web_package = "cobbler-web"
      $dnsmasq_package = "dnsmasq"
      $cobbler_service = "cobbler"
      $cobbler_web_service = "apache2"
      $cobbler_additional_packages = []
    }
  }

  define cobbler_safe_package(){
    if ! defined(Package[$name]){
      @package { $name : }
    }
  }

  cobbler_safe_package { $cobbler_additional_packages : }
  Package<||>

  package { $cobbler_package :
    ensure => installed,
    require => [
                Package[$dnsmasq_package],
                Package[$cobbler_additional_packages],
                ],
  }

  package { $cobbler_web_package :
    ensure => installed
  }

  package { $dnsmasq_package:
    ensure => installed
  }

  file { "/etc/init.d/dnsmasq":
    content => template("cobbler/dnsmasq.init.erb"),
    owner => root,
    group => root,
    mode => 0755,
    require => Package[$dnsmasq_package],
    notify => Service["dnsmasq"],
  }


  define access_to_cobbler_port($port, $protocol='tcp') {
    $rule = "-p $protocol -m state --state NEW -m $protocol --dport $port -j ACCEPT"
    exec { "access_to_cobbler_${protocol}_port: $port":
      command => "iptables -t filter -I INPUT 1 $rule; \
      /etc/init.d/iptables save",
      unless => "iptables -t filter -S INPUT | grep -q \"^-A INPUT $rule\""
    }
  }

  # OPERATING SYSTEM SPECIFIC ACTIONS
  case $operatingsystem {
    /(?i)(centos|redhat)/:{

      # HERE IS AN UGLY WORKAROUND TO MAKE COBBLER ABLE TO START
      # THERE IS AN ALTERNATIVE WAY TO ACHIEVE MAKE COBBLER STARTED
      # yum install policycoreutils-python
      # grep cobblerd /var/log/audit/audit.log | audit2allow -M cobblerpolicy
      # semodule -i cobblerpolicy.pp

      exec { "cobbler_disable_selinux":
        command => "setenforce 0",
        onlyif => "getenforce | grep -q Enforcing"
      }

      exec { "cobbler_disable_selinux_permanent":
        command => "sed -ie \"s/^SELINUX=enforcing/SELINUX=disabled/g\" /etc/selinux/config",
        onlyif => "grep -q \"^SELINUX=enforcing\" /etc/selinux/config"
      }


      # HERE IS IPTABLES RULES TO MAKE COBBLER AVAILABLE FROM OUTSIDE
      # https://github.com/cobbler/cobbler/wiki/Using%20Cobbler%20Import
      # SSH
      access_to_cobbler_port { "ssh":        port => '22' }
      # DNS
      access_to_cobbler_port { "dns_tcp":    port => '53' }
      access_to_cobbler_port { "dns_udp":    port => '53',  protocol => 'udp' }
      # DHCP
      access_to_cobbler_port { "dncp_67":    port => '67',  protocol => 'udp' }
      access_to_cobbler_port { "dncp_68":    port => '68',  protocol => 'udp' }
      # TFTP
      access_to_cobbler_port { "tftp_tcp":   port => '69' }
      access_to_cobbler_port { "tftp_udp":   port => '69',  protocol => 'udp' }
      # NTP
      access_to_cobbler_port { "ntp_udp":    port => '123', protocol => 'udp' }
      # HTTP/HTTPS
      access_to_cobbler_port { "http":       port => '80' }
      access_to_cobbler_port { "https":      port => '443'}
      # SYSLOG FOR COBBLER
      access_to_cobbler_port { "syslog_tcp": port => '25150'}
      # xmlrpc API
      access_to_cobbler_port { "xmlrpc_api": port => '25151' }

      service { "xinetd":
        enable => true,
        ensure => running,
        hasrestart => true,
        require => Package[$cobbler_additional_packages],
      }

      file { "/etc/xinetd.conf":
        content => template("cobbler/xinetd.conf.erb"),
        owner => root,
        group => root,
        mode => 0600,
        require => Package[$cobbler_additional_packages],
        notify => Service["xinetd"],
      }

    }
  }

  Service[$cobbler_service] -> Exec["cobbler_sync"] -> Service["dnsmasq"]

  service { $cobbler_service:
    enable => true,
    ensure => running,
    hasrestart => true,
    require => Package[$cobbler_package],
  }

  service { "dnsmasq":
    enable => true,
    ensure => running,
    hasrestart => true,
    require => Package[$dnsmasq_package],
    subscribe => Exec["cobbler_sync"],
  }

  service { $cobbler_web_service:
    enable => true,
    ensure => running,
    hasrestart => true,
    require => Package[$cobbler_web_package],
  }

  exec {"cobbler_sync":
    command => "cobbler sync",
    refreshonly => true,
    returns => [0, 155],
    require => [
                Package[$cobbler_package],
                Package[$dnsmasq_package],
                ],
    notify => Service["dnsmasq"],
    subscribe => Service[$cobbler_service],
  }

  file { "/etc/cobbler/modules.conf":
    content => template("cobbler/modules.conf.erb"),
    owner => root,
    group => root,
    mode => 0644,
    require => [
                Package[$cobbler_package],
                ],
    notify => [
               Service[$cobbler_service],
               Exec["cobbler_sync"],
               ],
  }

  file {"/etc/cobbler/settings":
    content => template("cobbler/settings.erb"),
    owner => root,
    group => root,
    mode => 0644,
    require => Package[$cobbler_package],
    notify => [
               Service[$cobbler_service],
               Exec["cobbler_sync"],
               ],
  }

  file {"/etc/cobbler/dnsmasq.template":
    content => template("cobbler/dnsmasq.template.erb"),
    owner => root,
    group => root,
    mode => 0644,
    require => [
                Package[$cobbler_package],
                Package[$dnsmasq_package],
                ],
    notify => [
               Service[$cobbler_service],
               Exec["cobbler_sync"],
               Service["dnsmasq"],
               ],

  }

  cobbler_digest_user {"cobbler":
    password => $cobbler_password,
    require => Package[$cobbler_package],
    notify => Service[$cobbler_service],
  }

  file {"/etc/cobbler/pxe/pxedefault.template":
    content => template("cobbler/pxedefault.template.erb"),
    owner => root,
    group => root,
    mode => 0644,
    require => Package[$cobbler_package],
    notify => [
               Service[$cobbler_service],
               Exec["cobbler_sync"],
               ],
  }

  file {"/etc/cobbler/pxe/pxelocal.template":
    content => template("cobbler/pxelocal.template.erb"),
    owner => root,
    group => root,
    mode => 0644,
    require => Package[$cobbler_package],
    notify => [
               Service[$cobbler_service],
               Exec["cobbler_sync"],
               ],
  }

  exec { "/var/lib/tftpboot/chain.c32":
    command => "cp /usr/share/syslinux/chain.c32 /var/lib/tftpboot/chain.c32",
    unless => "test -e /var/lib/tftpboot/chain.c32",
    require => [
                Package[$cobbler_additional_packages],
                Package[$cobbler_package],
                ]
  }


  define cobbler_snippet(){
    file {"/var/lib/cobbler/snippets/${name}":
      content => template("cobbler/snippets/${name}.erb"),
      owner => root,
      group => root,
      mode => 0644,
      require => Package[$cobbler::server::cobbler_package],
    }
  }
  }
