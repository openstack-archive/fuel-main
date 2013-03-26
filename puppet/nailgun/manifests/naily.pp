class nailgun::naily(
  $rabbitmq_naily_user = 'naily',
  $rabbitmq_naily_password = 'naily',
  $version,
  $gem_source = "http://rubygems.org/",
  ){

  exec { 'install-naily-gem':
    command => "/opt/rbenv/bin/rbenv exec gem install naily --source $gem_source --version $version --no-ri --no-rdoc",
    environment => ['RBENV_ROOT=/opt/rbenv', 'RBENV_VERSION=1.9.3-p392'],
    require => Exec['configure-rubygems'],
    logoutput => true,
  }

  exec { 'configure-rubygems':
    command => '/opt/rbenv/bin/rbenv exec gem sources -r http://rubygems.org/',
    environment => ['RBENV_ROOT=/opt/rbenv', 'RBENV_VERSION=1.9.3-p392'],
    require => Package['rbenv-ruby-1.9.3-p392-0.0.1-1'],
    logoutput => true,
  }

  package { 'rbenv-ruby-1.9.3-p392-0.0.1-1': }

  file { '/usr/bin/nailyd':
    content => template('nailgun/nailyd.erb'),
    owner => 'root',
    group => 'root',
    mode => 0755,
  }

  file { '/usr/bin/astute':
    content => template('nailgun/astute.erb'),
    owner => 'root',
    group => 'root',
    mode => 0755,
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
