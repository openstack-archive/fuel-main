class nailgun::cobbler(
  $cobbler_user = "cobbler",
  $cobbler_password = "cobbler",

  $centos_iso,
  $centos_repos,
  ){

  anchor { "nailgun-cobbler-begin": }
  anchor { "nailgun-cobbler-end": }

  Anchor<| title == "nailgun-cobbler-begin" |> ->
  Class["cobbler::server"] ->
  Class["cobbler::distro::centos63-x86_64"] ->
  Class["cobbler::profile::centos63-x86_64"] ->
  Anchor<| title == "nailgun-cobbler-end" |>
  
  class { "cobbler::server":
    server              => $ipaddress,
    
    domain_name         => $domain,
    name_server         => $ipaddress,
    next_server         => $ipaddress,
    
    dhcp_start_address  => ipcalc_network_nth_address($ipaddress, $netmask, "first"),
    dhcp_end_address    => ipcalc_network_nth_address($ipaddress, $netmask, "last"),
    dhcp_netmask        => $netmask,
    dhcp_gateway        => $ipaddress,
    dhcp_interface      => 'eth0',

    cobbler_user        => $cobbler_user,
    cobbler_password    => $cobbler_password,
    
    pxetimeout          => '50'
  }
        
  class { "cobbler::distro::centos63-x86_64":
    http_iso => $centos_iso,
    ks_url   => "cobbler",
  }

  class { "cobbler::profile::centos63-x86_64":
    ks_repo => $centos_repos,
  }

  cobbler_distro { "bootstrap":
    kernel => "${repo_root}/bootstrap/linux",
    initrd => "${repo_root}/bootstrap/initramfs.img",
    arch => "x86_64",
    breed => "redhat",
    osversion => "rhel6",
    ksmeta => "",
    require => Class["cobbler::server"],
  }
  
  cobbler_profile { "bootstrap":
    distro => "bootstrap",
    menu => true,
    kickstart => "",
    kopts => "",
    ksmeta => "",
    require => Cobbler_distro["bootstrap"],
  }

  exec { "cobbler_system_add_default":
    command => "cobbler system add --name=default \
    --profile=bootstrap --netboot-enabled=True",
    onlyif => "test -z `cobbler system find --name=default`",
    require => Cobbler_profile["bootstrap"],
  } 

  exec { "cobbler_system_edit_default":
    command => "cobbler system edit --name=default \
    --profile=bootstrap --netboot-enabled=True",
    onlyif => "test ! -z `cobbler system find --name=default`",
    require => Cobbler_profile["bootstrap"],
  }

  file { "/etc/cobbler/power/power_ssh.template":
    content => template("nailgun/power_ssh.template.erb"),
    owner => 'root',
    group => 'root',
    mode => 0644,
    require => Class["cobbler::server"],
  }
  
}
