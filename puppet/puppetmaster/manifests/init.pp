class puppetmaster (
  $puppet_master_hostname,
  $puppet_package_version = "2.7.19-1.el6",
  ) {
  anchor { "puppetmaster-begin": }
  anchor { "puppetmaster-end": }

  Anchor<| title == "puppetmaster-begin" |> ->
  Class["puppetmaster::selinux"] ->
  Class["puppetmaster::iptables"] ->
  Class["puppetmaster::master"] ->
  Class["puppetmaster::nginx"] ->
  Anchor<| title == "puppetmaster-end" |>


  class { "puppetmaster::selinux": }

  class { "puppetmaster::iptables": }

  class { "puppetmaster::master":
    puppet_master_hostname => $puppet_master_hostname,
    puppet_master_ports => "18140 18141 18142 18143",
    puppet_master_extra_opts => "--debug",
  }

  class { "puppetmaster::nginx":
    puppet_master_hostname => $puppet_master_hostname,
  }

}
