node default {
  class { "rpmcache":
    releasever => "6Server",
    pkgdir => "/var/www/nailgun/rhel",
    rh_username => "your_rh_username",
    rh_password => "your_rh_password",
    rh_base_channels => "rhel-6-server-rpms rhel-6-server-optional-rpms rhel-lb-for-rhel-6-server-rpms rhel-rs-for-rhel-6-server-rpms rhel-ha-for-rhel-6-server-rpms rhel-server-ost-6-folsom-rpms",
    #rh_openstack_channel => "rhel-server-ost-6-folsom-rpms",
    rh_openstack_channel => "rhel-server-ost-6-3-rpms",
    use_satellite => false,
    sat_hostname => undef,
    activation_key => undef
  }
}
