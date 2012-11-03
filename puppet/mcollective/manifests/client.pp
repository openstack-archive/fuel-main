class mcollective::client(
  $pskey = "secret",
  $stompuser = "mcollective",
  $stomppassword = "mcollective",
  $stomphost = "127.0.0.1",
  $stompport = "61613",
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
