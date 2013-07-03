node default {
  $rh_base_channels = "rhel-6-server-rpms rhel-6-server-optional-rpms rhel-lb-for-rhel-6-server-rpms rhel-rs-for-rhel-6-server-rpms rhel-ha-for-rhel-6-server-rpms rhel-server-ost-6-folsom-rpms"
  $rh_openstack_channel = "rhel-server-ost-6-3-rpms"
  $numtries = "3"
  $sat_base_channels = "rhel-x86_64-server-6 rhel-x86_64-server-optional-6 rhel-x86_64-server-lb-6 rhel-x86_64-server-rs-6 rhel-x86_64-server-ha-6"
  $sat_openstack_channel = "rhel-x86_64-server-6-ost-3"

  class { "rpmcache":
    releasever => "6Server",
    pkgdir => "/var/www/nailgun/rhel/6.4/nailgun/x86_64",
    rh_username => "your_rh_username",
    rh_password => "your_rh_password",
    rh_base_channels => $rh_base_channels,
    rh_openstack_channel => $rh_openstack_channel,
    use_satellite => false,
    sat_hostname => undef,
    activation_key => undef,
    sat_base_channels => $sat_base_channels,
    sat_openstack_channel => $sat_openstack_channel
  }
}

