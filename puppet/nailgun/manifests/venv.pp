class nailgun::venv(
  $venv,
  $venv_opts = "",
  $package,
  $version,
  $pip_opts = "",
  ) {

  nailgun::venv::venv { $venv:
    ensure => "present",
    venv => $venv,
    opts => $venv_opts,
    require => Package["python-virtualenv"],
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
  
  }
