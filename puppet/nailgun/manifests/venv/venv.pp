define nailgun::venv::venv(
  $venv,
  $opts = "",
  $owner = undef,
  $group = undef,
  $ensure = "present",
  $pip_opts = "",
  ) {


  if $ensure == 'present' {
    $root_parent = inline_template("<%= venv.match(%r!(.+)/.+!)[1] %>")

    if !defined(File[$root_parent]) {
      file { $root_parent:
        ensure => directory,
        recurse => true
      }
    }

    Exec {
      user => $owner,
      group => $group,
      cwd => "/tmp",
    }

    exec { "nailgun::venv $root":
      command => "virtualenv ${opts} ${venv}",
      creates => $venv,
      notify => Exec["update distribute and pip in $venv"],
      require => [File[$root_parent],
                  Package["python-virtualenv"]],
    }

    exec { "update distribute and pip in $venv":
      command => "$venv/bin/pip install ${pip_opts} -U distribute pip",
      refreshonly => true,
      returns => [0, 1],
    }

    }

    elsif $ensure == 'absent' {

      file { $venv:
        ensure => $ensure,
        recurse => true,
        purge => true,
        force => true,
      }
    }

}
