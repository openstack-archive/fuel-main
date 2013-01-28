class puppetmaster (
  $puppet_master_hostname,
  $puppet_package_version = "2.7.19-1.el6",
  $gem_source = "http://rubygems.org/",
  ) {
  anchor { "puppetmaster-begin": }
  anchor { "puppetmaster-end": }

  Anchor<| title == "puppetmaster-begin" |> ->
  Class["puppetmaster::selinux"] ->
  Class["puppetmaster::iptables"] ->
  Class["puppetmaster::packages"] ->
  Class["puppetmaster::master"] ->
  Class["puppetmaster::nginx"] ->
  Anchor<| title == "puppetmaster-end" |>


  class { "puppetmaster::selinux": }

  class { "puppetmaster::iptables": }

  class { "puppetmaster::packages":
    puppet_package_version => $puppet_package_version,
    gem_source => $gem_source,
  }

  class { "puppetmaster::master":
    puppet_master_hostname => $puppet_master_hostname,
    puppet_master_ports => "18140 18141 18142 18143",
  }

  class { "puppetmaster::nginx":
    puppet_master_hostname => $puppet_master_hostname,
  }

}
