class nailgun::logrotate {

  file { "/etc/logrotate.d/nailgun":
    content => template("nailgun/logrotate.conf.erb"),
  }

  file {"/var/log/nailgun":
    ensure => directory,
    owner => 'root',
    group => 'root',
    mode => 0755,
  }

}
