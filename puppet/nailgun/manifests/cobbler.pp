class nailgun::cobbler(
  $cobbler_user = "cobbler",
  $cobbler_password = "cobbler",

  $centos_iso,
  $centos_repos,

  $ks_system_timezone         = "America/Los_Angeles",

  # default password is 'r00tme'
  $ks_encrypted_root_password = "\$6\$tCD3X7ji\$1urw6qEMDkVxOkD33b4TpQAjRiCeDZx0jmgMhDYhfB9KuGfqO9OcMaKyUxnGGWslEDQ4HxTw7vcAMP85NxQe61",

  ){

  anchor { "nailgun-cobbler-begin": }
  anchor { "nailgun-cobbler-end": }

  Anchor<| title == "nailgun-cobbler-begin" |> ->
  Class["cobbler::server"] ->
  Class["cobbler::distro::centos63-x86_64"] ->
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

  # ADDING send2syslog.py SCRIPT AND CORRESPONDING SNIPPET

  file { "/var/www/cobbler/aux/send2syslog.py":
    content => template("nailgun/cobbler/send2syslog.py"),
    owner => "root",
    group => "root",
    mode => 0644,
    require => Class["cobbler::server"],
  }

  file {"/var/lib/cobbler/snippets/send2syslog.snippet":
    content => template("nailgun/cobbler/send2syslog.snippet.erb"),
    owner => root,
    group => root,
    mode => 0644,
    require => Class["cobbler::server"],
  }

  # THIS VARIABLE IS NEEDED FOR TEMPLATING centos63-x86_64.ks
  $ks_repo = $centos_repos

  file { "/var/lib/cobbler/kickstarts/centos63-x86_64.ks":
    content => template("nailgun/cobbler/centos.ks.erb"),
    owner => root,
    group => root,
    mode => 0644,
    require => Class["cobbler::server"],
  } ->

  cobbler_profile { "centos63-x86_64":
    kickstart => "/var/lib/cobbler/kickstarts/centos63-x86_64.ks",
    kopts => "",
    distro => "centos63-x86_64",
    ksmeta => "",
    menu => true,
    require => Class["cobbler::server"],
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
    kopts => "url=http://${ipaddress}:8000/api",
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
