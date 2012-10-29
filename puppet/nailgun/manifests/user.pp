class nailgun::user(
  $nailgun_group = "nailgun",
  $nailgun_user = "nailgun",
  ) {

  group { $nailgun_group :
    provider => "groupadd",
    ensure => "present",
  }

  user { $nailgun_user :
    ensure => "present",
    gid => $nailgun_group,
    home => "/",
    shell => "/bin/false",
    require => Group[$nailgun_group],
  }

}
