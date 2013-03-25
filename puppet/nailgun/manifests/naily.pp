class nailgun::naily(
  $rabbitmq_naily_user = 'naily',
  $rabbitmq_naily_password = 'naily',
  $version,
  $gem_source = "http://rubygems.org/",
  ){

  package { 'rbenv-ruby-1.9.3-p392-0.0.1-1': }

  exec { "rbenv exec gem install naily --source #{$gem_source} --version #{$version} --no-ri --no-rdoc":
    environment => ['RBENV_ROOT=/opt/rbenv', 'RBENV_VERSION=1.9.3-p392'],
    path => ['/opt/rbenv/bin']
  }

  file { '/usr/bin/nailyd':
    content => template('nailgun/nailyd.erb'),
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
