class nailgun::naily(
  $rabbitmq_naily_user = 'naily',
  $rabbitmq_naily_password = 'naily',
  $version,
  $gem_source = "http://rubygems.org/",
  ){

  package { "naily":
    provider => "gem",
    ensure => $version,
    source => $gem_source,
  }

  file {"/etc/naily":
    ensure => directory,
    owner => 'root',
    group => 'root',
    mode => 0755,
  }

  file {"/etc/naily/nailyd.conf":
    content => template("nailgun/nailyd.conf.erb"),
    owner => 'root',
    group => 'root',
    mode => 0644,
    require => File["/etc/naily"],
  }

  file {"/var/log/naily":
    ensure => directory,
    owner => 'root',
    group => 'root',
    mode => 0755,
  }

}
