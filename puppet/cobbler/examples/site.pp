node default {
  notify { "test-notification-${hostname}": }
}

node /^(fuel-pm|fuel-cobbler).mirantis.com/ {

  Exec  {path => '/usr/bin:/bin:/usr/sbin:/sbin'}
  
  exec { "enable_forwarding":
    command => "echo 1 > /proc/sys/net/ipv4/ip_forward",
    unless => "cat /proc/sys/net/ipv4/ip_forward | grep -q 1",
  }

  exec { "enable_nat_all":
    command => "iptables -t nat -I POSTROUTING 1 -s 10.0.0.0/24 ! -d 10.0.0.0/24 -j MASQUERADE; \
    /etc/init.d/iptables save",
    unless => "iptables -t nat -S POSTROUTING | grep -q \"^-A POSTROUTING -s 10.0.0.0/24 ! -d 10.0.0.0/24 -j MASQUERADE\""
  }
  
  exec { "enable_nat_filter":
    command => "iptables -t filter -I FORWARD 1 -j ACCEPT; \
    /etc/init.d/iptables save",
    unless => "iptables -t filter -S FORWARD | grep -q \"^-A FORWARD -j ACCEPT\""
  }
  
  class { cobbler::server:
    server              => '10.0.0.100',

    domain_name         => 'mirantis.com',
    name_server         => '10.0.0.100',
    next_server         => '10.0.0.100',

    dhcp_start_address  => '10.0.0.201',
    dhcp_end_address    => '10.0.0.254',
    dhcp_netmask        => '255.255.255.0',
    dhcp_gateway        => '10.0.0.100',
    dhcp_interface      => 'eth1',
    
    cobbler_user        => 'cobbler',
    cobbler_password    => 'cobbler',

    pxetimeout          => '0'
  }

  Class[cobbler::server] ->
  Class[cobbler::distro::centos63-x86_64]

  # class { cobbler::distro::centos63-x86_64:
  #   http_iso => "http://10.100.0.1/iso/CentOS-6.3-x86_64-netinstall.iso",
  #   ks_url   => "http://172.18.8.52/~hex/centos/6.3/os/x86_64",
  # }

  class { cobbler::distro::centos63-x86_64:
    http_iso => "http://10.0.0.1/iso/CentOS-6.3-x86_64-minimal.iso",
    ks_url   => "cobbler",
  }

  
  Class[cobbler::distro::centos63-x86_64] ->
  Class[cobbler::profile::centos63-x86_64]

  class { cobbler::profile::centos63-x86_64: }

  # RHEL distribution
  # class { cobbler::distro::rhel63-x86_64:
  #   http_iso => "http://address/of/rhel-server-6.3-x86_64-boot.iso",
  #   ks_url   => "http://address/of/rhel/base/mirror/6.3/os/x86_64",
  # }
  #
  # Class[cobbler::distro::rhel63-x86_64] ->
  # Class[cobbler::profile::rhel63-x86_64]
  #
  # class { cobbler::profile::rhel63-x86_64: }



  # IT IS NEEDED IN ORDER TO USE cobbler_system.py SCRIPT
  # WHICH USES argparse PYTHON MODULE
  package {"python-argparse": }

}
