class mcollective::client(
  $pskey = "secret",
  $user = "mcollective",
  $password = "mcollective",
  $host = "127.0.0.1",
  $stompport = "61613",
  $port = "5672",
  $vhost = "mcollective",
  $stomp = false,
  ){

  case $operatingsystem {
    /(?i)(centos|redhat)/:  {
      # THIS PACKAGE ALSO INSTALLS REQUIREMENTS
      # mcollective-common
      # rubygems
      # rubygem-stomp
      $mcollective_client_package = "mcollective-client"
    }
    default: {
      fail("Unsupported operating system: ${operatingsystem}")
    }
  }

  package { $mcollective_client_package : }
  package { 'nailgun-mcagents': }

  file {"/etc/mcollective/client.cfg" :
    content => template("mcollective/client.cfg.erb"),
    owner => root,
    group => root,
    mode => 0600,
    require => Package[$mcollective_client_package],
  }

  }
