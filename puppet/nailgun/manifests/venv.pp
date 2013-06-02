class nailgun::venv(
  $venv,
  $venv_opts = "",
  $package,
  $version,
  $pip_opts = "",

  $nailgun_user,
  $nailgun_group,

  $database_name,
  $database_engine,
  $database_host,
  $database_port,
  $database_user,
  $database_passwd,

  $staticdir,
  $templatedir,

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

  Nailgun::Venv::Pip {
    require => [
      Nailgun::Venv::Venv[$venv],
      Package["python-devel"],
      Package["gcc"],
      Package["make"],
    ],
    opts => $pip_opts,
    venv => $venv,
  }

  nailgun::venv::pip { "$venv_$package":
    package => "$package==$version",
  }

  nailgun::venv::pip { "psycopg2":
    package => "psycopg2==2.4.6",
    require => [
      Package["postgresql-devel"],
      Nailgun::Venv::Venv[$venv],
      Package["python-devel"],
      Package["gcc"],
      Package["make"],
    ],
  }

  file { "/etc/nailgun":
    ensure => directory,
    owner => 'root',
    group => 'root',
    mode => 0755,
  }

  $exclude_network = ipcalc_network_by_address_netmask($ipaddress, $netmask)
  $exclude_cidr = ipcalc_network_cidr_by_netmask($netmask)

  $admin_network = ipcalc_network_by_address_netmask($ipaddress, $netmask)
  $admin_network_cidr = ipcalc_network_cidr_by_netmask($netmask)
  $admin_network_size = ipcalc_network_count_addresses($ipaddress, $netmask)
  $first_in_second_half = ipcalc_network_count_addresses($ipaddress, $netmask) / 2 + 1
  $admin_network_first = ipcalc_network_nth_address($ipaddress, $netmask, $first_in_second_half)
  $admin_network_last = ipcalc_network_nth_address($ipaddress, $netmask, "last")
  $admin_network_netmask = $netmask

  file { "/etc/nailgun/settings.yaml":
    content => template("nailgun/settings.yaml.erb"),
    owner => 'root',
    group => 'root',
    mode => 0644,
    require => File["/etc/nailgun"],
  }

  exec {"nailgun_syncdb":
    command => "${venv}/bin/nailgun_syncdb",
    require => [
                File["/etc/nailgun/settings.yaml"],
                Nailgun::Venv::Pip["$venv_$package"],
                Nailgun::Venv::Pip["psycopg2"],
                Class["nailgun::database"],
                ],
  }

  exec {"nailgun_upload_fixtures":
    command => "${venv}/bin/nailgun_fixtures",
    require => Exec["nailgun_syncdb"],
  }

  }
