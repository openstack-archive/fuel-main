class puppetmaster::master (
  $puppet_master_hostname,
  $puppet_master_ports = "18140 18141 18142 18143",
  $puppet_master_log = "syslog",
  $puppet_master_extra_opts = "",
  ) inherits puppetmaster::params {

  package { $puppetmaster::params::puppet_master_packages :
    ensure => $puppet_master_version,
  }
  package { $puppetmaster::params::mongrel_packages :
    ensure => present,
  }



  file { "/etc/sysconfig/puppetmaster":
    content => template("puppetmaster/sysconfig_puppetmaster.erb"),
    owner => 'root',
    group => 'root',
    mode => 0644,
    require => Package["puppet-server"],
    notify => Service["puppetmaster"],
  }

  if $puppet_master_log == "syslog" {
    file { "/etc/rsyslog.d/40-puppet-master.conf":
      content => "if \$programname == 'puppet-master' then /var/log/puppet/master.log",
      owner => "root",
      group => "root",
      mode => 0644,
    }->Service["rsyslog"]->Service["puppetmaster"]
  }

  file { "/etc/puppet/puppet.conf":
    content => template("puppetmaster/puppet.conf.erb"),
    owner => "puppet",
    group => "puppet",
    mode => 0600,
    require => Package["puppet-server"],
    notify => Service["puppetmaster"],
  }

  file { "/etc/puppet/puppetdb.conf":
    content => template("puppetmaster/puppetdb.conf.erb"),
    owner => "puppet",
    group => "puppet",
    mode => 0600,
    require => Package["puppet-server"],
    notify => Service["puppetmaster"],
  }
 
 package {"puppetdb-terminus": ensure => present }

  service { "puppetmaster":
    enable => true,
    ensure => "running",
    require => [
                Package["puppet-server"],
                Package["rubygem-mongrel"],
                Package["puppetdb-terminus"],
                ],
  }

}
