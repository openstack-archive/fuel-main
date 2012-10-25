class nailgun(
  $package,
  $version,
  $nailgun_group = "nailgun",
  $nailgun_user = "nailgun",
  $venv = "/opt/nailgun",

  $pip_index = "",
  $pip_find_links = "",
  $gem_repo = "/var/www/gems",
  
  $databasefile = "/var/tmp/nailgun.sqlite",
  $staticdir = "/opt/nailgun/usr/share/nailgun/static",
  $templatedir = "/opt/nailgun/usr/share/nailgun/static",
  $logfile = "/var/log/nailgun/nailgun.log",
  $rundir = "/var/run/nailgun",
  
  $cobbler_url = "http://localhost/cobbler_api",
  $cobbler_user = "cobbler",
  $cobbler_password = "cobbler",

  $mco_pskey = "123456",
  $mco_stompuser = "mcollective",
  $mco_stomppassword = "mcollective",

  $naily_user = "naily",
  $naily_password = "naily",
  
  $puppet_master_host = "${hostname}.${domain}",
  
  ) {

  $logparentdir = inline_template("<%= logfile.match(%r!(.+)/.+!)[1] %>")
  $database_engine = "sqlite:///${databasefile}"
  
  anchor { "nailgun-begin": }
  anchor { "nailgun-end": }

  Anchor<| title == "nailgun-begin" |> ->
  Class["nailgun::packages"] ->
  Class["nailgun::iptables"] ->
  Class["nailgun::user"] ->
  Class["nailgun::venv"] ->
  Class["nailgun::nginx"] ->
  Class["nailgun::supervisor"] ->
  Anchor<| title == "nailgun-end" |>
  
  class { "nailgun::packages": }

  class { "nailgun::iptables": }
  
  class { "nailgun::user":
    nailgun_group => $nailgun_group,
    nailgun_user => $nailgun_user,
  }
  
  class { "nailgun::venv":
    venv => $venv,
    venv_opts => "--system-site-packages",
    package => $package,
    version => $version,
    pip_opts => "${pip_index} ${pip_find_links}"
  }

  class { "nailgun::supervisor":
    venv => $venv,
  }

  class { "nailgun::nginx":
    staticdir => $staticdir,
    rundir => $rundir,
  }

  file { $logparentdir:
    ensure => directory,
    recurse => true,
    owner => 'root',
    group => 'root',
    mode => 0755,
  }

  file { $rundir:
    ensure => directory,
    owner => $nailgun_user,
    group => $nailgun_group,
    mode => 0755,
  }
  
  file { "/etc/nailgun":
    ensure => directory,
    owner => 'root',
    group => 'root',
    mode => 0755,
  }

  file { "/etc/nailgun/settings.yaml":
    content => template("nailgun/settings.yaml.erb"),
    owner => 'root',
    group => 'root',
    mode => 0644,
    require => File["/etc/nailgun"],
  }

  exec {"nailgun_syncdb":
    command => "${venv}/bin/nailgun_syncdb",
    creates => $databasefile,
    require => [
                File["/etc/nailgun/settings.yaml"],
                Class["nailgun::venv"],
                ]
  }

  rabbitmq_user { $naily_user:
    admin     => true,
    password  => $naily_password,
    provider  => 'rabbitmqctl',
    require   => Class['rabbitmq::server'],
  }
  
  rabbitmq_user_permissions { "${naily_user}@/":
    configure_permission => '.*',
    write_permission     => '.*',
    read_permission      => '.*',
    provider             => 'rabbitmqctl',
    require              => Class['rabbitmq::server'],
  }

}
