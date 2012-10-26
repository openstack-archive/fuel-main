class puppetmaster::master (
  $puppet_master_hostname,
  $puppet_stored_dbname,
  $puppet_stored_dbuser,
  $puppet_stored_dbpassword,
  $puppet_stored_dbsocket,

  $puppet_master_ports = "18140 18141 18142 18143",
  ){

  file { "/etc/sysconfig/puppetmaster":
    content => template("puppetmaster/sysconfig_puppetmaster.erb"),
    owner => 'root',
    group => 'root',
    mode => 0644,
    require => Package["puppet-server"],
    notify => Service["puppetmaster"],
  }

  file { "/etc/puppet/puppet.conf":
    content => template("puppetmaster/puppet.conf.erb"),
    owner => "puppet",
    group => "puppet",
    mode => 0600,
    require => Package["puppet-server"],
    notify => Service["puppetmaster"],
  }

  service { "puppetmaster":
    enable => true,
    ensure => "running",
    require => [
                Package["puppet-server"],
                Package["rubygem-mongrel"],
                ],
  }

  }
