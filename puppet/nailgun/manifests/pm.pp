class nailgun::pm(
  $puppet_master_hostname = "${hostname}.${domain}",
  ){

  class { "puppetmaster":
    puppet_master_hostname => $puppet_master_hostname,
  }

}
