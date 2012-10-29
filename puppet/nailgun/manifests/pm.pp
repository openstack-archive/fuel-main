class nailgun::pm(
  $puppet_master_hostname = "${hostname}.${domain}",
  $gem_source = "http://rubygems.org/",
  ){

  class { "puppetmaster":
    puppet_master_hostname => $puppet_master_hostname,
    gem_source => $gem_source,
  }

}
