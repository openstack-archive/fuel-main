class nailgun::nginx-nailgun(
  $staticdir,
  ) {

  file { "/etc/nginx/conf.d/nailgun.conf":
    content => template("nailgun/nginx_nailgun.conf.erb"),
    owner => 'root',
    group => 'root',
    mode => 0644,
    require => Package["nginx"],
    notify => Service["nginx"],
  }

}
