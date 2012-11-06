class nailgun::venv(
  $venv,
  $venv_opts = "",
  $package,
  $version,
  $pip_opts = "",

  $nailgun_user,
  $nailgun_group,
  $databasefile,
  $staticdir,
  $templatedir,
  $logfile,

  $rabbitmq_naily_user,
  $rabbitmq_naily_password,
  ) {

  nailgun::venv::venv { $venv:
    ensure => "present",
    venv => $venv,
    opts => $venv_opts,
    require => Package["python-virtualenv"],
    pip_opts => $pip_opts,
  }

  nailgun::venv::pip { "$venv_$package":
    package => "$package==$version",
    opts => $pip_opts,
    venv => $venv,
    require => [
                Nailgun::Venv::Venv[$venv],
                Package["python-devel"],
                Package["gcc"],
                Package["make"],
                ]
  }

  $logparentdir = inline_template("<%= logfile.match(%r!(.+)/.+!)[1] %>")
  $databasefiledir = inline_template("<%= databasefile.match(%r!(.+)/.+!)[1] %>")
  $database_engine = "sqlite:///${databasefile}"

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

  if ! defined(File[$databasefiledir]){
    file { $logparentdir:
      ensure => directory,
      recurse => true,
    }
  }

  if ! defined(File[$databasefiledir]){
    file { $databasefiledir:
      ensure => directory,
      recurse => true,
    }
  }

  exec {"nailgun_syncdb":
    command => "${venv}/bin/nailgun_syncdb",
    creates => $databasefile,
    require => [
                File["/etc/nailgun/settings.yaml"],
                File[$databasefiledir],
                Nailgun::Venv::Pip["$venv_$package"],
                ],
  }

  exec {"nailgun_upload_fixtures":
    command => "${venv}/bin/nailgun_fixtures",
    require => Exec["nailgun_syncdb"],
  }

  }
