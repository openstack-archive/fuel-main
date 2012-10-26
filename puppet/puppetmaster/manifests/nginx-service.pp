class puppetmaster::nginx-service {

  service { "nginx":
    enable => true,
    ensure => "running",
    require => Package["nginx"],
  }

}
