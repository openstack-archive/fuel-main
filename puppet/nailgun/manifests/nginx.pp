class nailgun::nginx(
  $staticdir,
  $rundir,
  ) {

  file { "/etc/nginx/conf.d/nailgun.conf":
    content => template("nailgun/nginx_nailgun.conf.erb"),
    owner => 'root',
    group => 'root',
    mode => 0644,
    require => Package["nginx"],
    notify => Service["nginx"],
  }

  file { "/etc/nginx/conf.d/repo.conf":
    content => template("nailgun/nginx_nailgun_repo.conf.erb"),
    owner => 'root',
    group => 'root',
    mode => 0644,
    require => Package["nginx"],
    notify => Service["nginx"],
  }


  # service { "nginx":
  #   enable => true,
  #   ensure => "running",
  #   require => Package["nginx"]
  # }

}
