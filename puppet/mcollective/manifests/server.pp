class mcollective::server(
  $pskey = "secret",
  $user = "mcollective",
  $password = "mcollective",
  $host = "127.0.0.1",
  $stompport = "61613",
  $vhost = "mcollective",
  $stomp = false,
  ){

  case $operatingsystem {
    /(?i)(centos|redhat)/:  {
      # THIS PACKAGE ALSO INSTALLS REQUIREMENTS
      # mcollective-common
      # rubygems
      # rubygem-stomp
      $mcollective_package = "mcollective"
    }
    default: {
      fail("Unsupported operating system: ${operatingsystem}")
    }
  }

  package { $mcollective_package : }

  file {"/etc/mcollective/server.cfg" :
    content => template("mcollective/server.cfg.erb"),
    owner => root,
    group => root,
    mode => 0600,
    require => Package[$mcollective_package],
  }

  service { "mcollective":
    enable => true,
    ensure => "running",
    require => File["/etc/mcollective/server.cfg"],
  }

}
