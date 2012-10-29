class nailgun::supervisor(
  $venv,
  ) {

  file { "/etc/supervisord.conf":
    content => template("nailgun/supervisord.conf.erb"),
    owner => 'root',
    group => 'root',
    mode => 0644,
    require => Package["supervisor"],
    notify => Service["supervisord"],
  }

  service { "supervisord":
    ensure => "running",
    enable => true,
    require => [
                Package["supervisor"],
                Service["rabbitmq-server"],
                ],
  }

}
