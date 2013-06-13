class nailgun::cobbler(
  $cobbler_user = "cobbler",
  $cobbler_password = "cobbler",

  $centos_repos,
  $gem_source,

  $ks_system_timezone         = "Etc/UTC",

  # default password is 'r00tme'
  $ks_encrypted_root_password = "\$6\$tCD3X7ji\$1urw6qEMDkVxOkD33b4TpQAjRiCeDZx0jmgMhDYhfB9KuGfqO9OcMaKyUxnGGWslEDQ4HxTw7vcAMP85NxQe61",

  ){

  anchor { "nailgun-cobbler-begin": }
  anchor { "nailgun-cobbler-end": }

  Anchor<| title == "nailgun-cobbler-begin" |> ->
  Class["cobbler::server"] ->
  Anchor<| title == "nailgun-cobbler-end" |>

  $half_of_network = ipcalc_network_count_addresses($ipaddress, $netmask) / 2

  class { "cobbler::server":
    server              => $ipaddress,

    domain_name         => $domain,
    name_server         => $ipaddress,
    next_server         => $ipaddress,

    dhcp_start_address  => ipcalc_network_nth_address($ipaddress, $netmask, "first"),
    dhcp_end_address    => ipcalc_network_nth_address($ipaddress, $netmask, $half_of_network),
    dhcp_netmask        => $netmask,
    dhcp_gateway        => $ipaddress,
    dhcp_interface      => 'eth0',

    cobbler_user        => $cobbler_user,
    cobbler_password    => $cobbler_password,

    pxetimeout          => '50'
  }

  # ADDING send2syslog.py SCRIPT AND CORRESPONDING SNIPPET

  file { "/var/www/cobbler/aux/send2syslog.py":
    content => template("nailgun/cobbler/send2syslog.py"),
    owner => "root",
    group => "root",
    mode => 0644,
    require => Class["cobbler::server"],
  }

  file {"/var/lib/cobbler/snippets/send2syslog":
    content => template("nailgun/cobbler/send2syslog.snippet.erb"),
    owner => root,
    group => root,
    mode => 0644,
    require => Class["cobbler::server"],
  }

  file {"/var/lib/cobbler/snippets/target_logs_to_master":
    content => template("nailgun/cobbler/target_logs_to_master.snippet.erb"),
    owner => root,
    group => root,
    mode => 0644,
    require => Class["cobbler::server"],
  }

  file {"/var/lib/cobbler/snippets/kickstart_ntp":
    content => template("nailgun/cobbler/kickstart_ntp.snippet.erb"),
    owner => root,
    group => root,
    mode => 0644,
    require => Class["cobbler::server"],
  }

  file {"/var/lib/cobbler/snippets/ntp_to_masternode":
    content => template("nailgun/cobbler/ntp_to_masternode.snippet.erb"),
    owner => root,
    group => root,
    mode => 0644,
    require => Class["cobbler::server"],
  }

file {"/var/lib/cobbler/snippets/dhclient_ignore_routers_opt":
    content => template("nailgun/cobbler/dhclient_ignore_routers_opt.snippet.erb"),
    owner => root,
    group => root,
    mode => 0644,
    require => Class["cobbler::server"],
  }

  # THIS VARIABLE IS NEEDED FOR TEMPLATING centos-x86_64.ks
  $ks_repo = $centos_repos

  file { "/var/lib/cobbler/kickstarts/centos-x86_64.ks":
    content => template("nailgun/cobbler/centos.ks.erb"),
    owner => root,
    group => root,
    mode => 0644,
    require => Class["cobbler::server"],
  } ->

  cobbler_distro { "centos-x86_64":
    kernel => "${repo_root}/centos/fuelweb/x86_64/isolinux/vmlinuz",
    initrd => "${repo_root}/centos/fuelweb/x86_64/isolinux/initrd.img",
    arch => "x86_64",
    breed => "redhat",
    osversion => "rhel6",
    ksmeta => "tree=http://@@server@@:8080/centos/fuelweb/x86_64/",
    require => Class["cobbler::server"],
  }

  cobbler_profile { "centos-x86_64":
    kickstart => "/var/lib/cobbler/kickstarts/centos-x86_64.ks",
    kopts => "biosdevname=0",
    distro => "centos-x86_64",
    ksmeta => "",
    menu => true,
    require => Cobbler_distro["centos-x86_64"],
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
    kopts => "biosdevname=0 url=http://${ipaddress}:8000/api",
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

  exec { "nailgun_cobbler_sync":
    command => "cobbler sync",
    refreshonly => true,
  }

  Exec["cobbler_system_add_default"] ~> Exec["nailgun_cobbler_sync"]
  Exec["cobbler_system_edit_default"] ~> Exec["nailgun_cobbler_sync"]

  file { "/etc/cobbler/power/fence_ssh.template":
    content => template("nailgun/cobbler/fence_ssh.template.erb"),
    owner => 'root',
    group => 'root',
    mode => 0644,
    require => Class["cobbler::server"],
  }

  file { "/usr/sbin/fence_ssh":
    content => template("nailgun/cobbler/fence_ssh.erb"),
    owner => 'root',
    group => 'root',
    mode => 0755,
    require => Class["cobbler::server"],
  }

  file {"/var/lib/cobbler/snippets/authorized_keys":
    content => template("nailgun/cobbler/authorized_keys.snippet.erb"),
    owner => root,
    group => root,
    mode => 0644,
    require => Class["cobbler::server"],
  }

  file {"/var/lib/cobbler/snippets/pre_install_network_config":
    content => template("nailgun/cobbler/pre_install_network_config.snippet.erb"),
    owner => root,
    group => root,
    mode => 0644,
    require => Class["cobbler::server"],
  }

  file {"/var/lib/cobbler/snippets/pre_install_partition":
    content => template("nailgun/cobbler/pre_install_partition.snippet.erb"),
    owner => root,
    group => root,
    mode => 0644,
    require => Class["cobbler::server"],
  }

  file {"/var/lib/cobbler/snippets/pre_install_partition_lvm":
    content => template("nailgun/cobbler/pre_install_partition_lvm.snippet.erb"),
    owner => root,
    group => root,
    mode => 0644,
    require => Class["cobbler::server"],
  }

  file { "/var/lib/cobbler/snippets/nailgun_repo":
    content => template("nailgun/cobbler/nailgun_repo.snippet.erb"),
    owner => root,
    group => root,
    mode => 0644,
    require => Class["cobbler::server"],
  }

  file { "/var/lib/cobbler/snippets/ssh_disable_gssapi":
    content => template("nailgun/cobbler/ssh_disable_gssapi.snippet.erb"),
    owner => root,
    group => root,
    mode => 0644,
    require => Class["cobbler::server"],
  }

  file { "/var/lib/cobbler/snippets/sshd_auth_pubkey_only":
    content => template("nailgun/cobbler/sshd_auth_pubkey_only.snippet.erb"),
    owner => root,
    group => root,
    mode => 0644,
    require => Class["cobbler::server"],
  }

  Package<| title == "cman" |>
  Package<| title == "fence-agents"|>
}
