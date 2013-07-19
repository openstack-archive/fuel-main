class nailgun::gateone (
  $pip_opts = "",
){

  $venv = "/opt/gateone"
  $venv_opts = "--system-site-packages"
  $root = $venv

  nailgun::venv::venv { $venv:
    ensure => "present",
    venv => $venv,
    opts => $venv_opts,
    require => Package["python-virtualenv"],
    pip_opts => $pip_opts,
  }

  nailgun::venv::pip { "tornado":
    package => "tornado==3.0",
    opts => $pip_opts,
    venv => $venv,
    require => [
      Nailgun::Venv::Venv[$venv],
    ]
  }

  nailgun::venv::pip { "ordereddict":
    package => "ordereddict",
    opts => $pip_opts,
    venv => $venv,
    require => [
      Nailgun::Venv::Venv[$venv],
    ]
  }

  nailgun::venv::pip { "gateone":
    package => "gateone",
    opts => "${pip_opts} --install-option=\"--prefix=${venv}\"",
    venv => $venv,
    require => [
      Nailgun::Venv::Pip['tornado'],
      Nailgun::Venv::Pip['ordereddict'],
    ]
  }->
  
  file { "${venv}/gateone/settings/10server.conf":
    content => template("nailgun/gateone/10server.conf.erb"),
    owner => 'root',
    group => 'root',
    mode => 0644,
    require => [
        Nailgun::Venv::Pip['gateone'],
    ],
  }

  file { "${venv}/gateone/settings/50terminal.conf":
    content => template("nailgun/gateone/50terminal.conf.erb"),
    owner => 'root',
    group => 'root',
    mode => 0644,
    require => [
        Nailgun::Venv::Pip['gateone'],
    ],
  }

  file { "${venv}/gateone/applications/terminal/plugins/ssh/scripts/ssh_connect.py":
    mode => 755,
    require => [
        Nailgun::Venv::Pip['gateone'],
    ],
  }

  service { "gateone":
    ensure => "running",
    enable => true,
    require => File['/etc/init.d/gateone'],
  }

  file { "/etc/init.d/gateone":
    content => template("nailgun/gateone/init.erb"),
    owner => 'root',
    group => 'root',
    require => [
        Nailgun::Venv::Pip['gateone'],
    ],
    mode => 0755,
  }

  file { [ "${venv}/users/", "${venv}/users/ANONYMOUS/",
           "${venv}/users/ANONYMOUS/.ssh"
         ]:
    ensure => "directory",
    require => [
      Nailgun::Venv::Venv[$venv],
    ],
  }

  file { "${venv}/users/ANONYMOUS/.ssh/config":
    content => template("nailgun/gateone/config.erb"),
    owner => 'root',
    group => 'root',
    mode => 0644,
  } 

  file { "${venv}/users/ANONYMOUS/.ssh/.default_ids":
    content => template("nailgun/gateone/default_ids.erb"),
    owner => 'root',
    group => 'root',
    mode => 0644,
  } -> 

  exec { "create_gateone_key":
    command => "cp /root/.ssh/*rsa* ${venv}/users/ANONYMOUS/.ssh/",
    onlyif => "test -f /root/.ssh/id_rsa",
  } ->

  exec { "generate_bootstrap_public_key":
    command => "ssh-keygen -f ${venv}/users/ANONYMOUS/.ssh/bootstrap.rsa -y \
                    > ${venv}/users/ANONYMOUS/.ssh/bootstrap.rsa.pub",
  }
}
