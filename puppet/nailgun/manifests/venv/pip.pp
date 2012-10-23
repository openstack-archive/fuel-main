define nailgun::venv::pip(
  $package,
  $venv,
  $opts = "",
  $ensure = "present",
  $owner = undef,
  $group = undef,
  ) {
    
  $grep_regex = $package ? {
    /==/ => "^${package}\$",
    default => "^${package}==",
  }
    
  Exec {
    user => $owner,
    group => $group,
    cwd => "/tmp",
  }
  
  if $ensure == 'present' {
    exec { "$venv/bin/pip install $name":
      command => "$venv/bin/pip install $opts $package",
      unless => "$venv/bin/pip freeze | grep -e $grep_regex"
    }
  }
  elsif $ensure == 'latest' {
    exec { "pip install $name":
      command => "$venv/bin/pip install $opts -U $package",
    }
  }
  else {
    exec { "pip install $name":
      command => "$venv/bin/pip uninstall $package",
      onlyif => "$venv/bin/pip freeze | grep -e $grep_regex"
    }
  }
  }
