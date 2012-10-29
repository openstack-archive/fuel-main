class nailgun(
  $package,
  $version,
  $nailgun_group = "nailgun",
  $nailgun_user = "nailgun",
  $venv = "/opt/nailgun",

  $repo_root = "/var/www/nailgun",
  $pip_index = "",
  $pip_find_links = "",
  $gem_source = "http://localhost/gems/",

  $databasefile = "/var/tmp/nailgun.sqlite",
  $staticdir = "/opt/nailgun/usr/share/nailgun/static",
  $templatedir = "/opt/nailgun/usr/share/nailgun/static",
  $logfile = "/var/log/nailgun/nailgun.log",

  $cobbler_url = "http://localhost/cobbler_api",
  $cobbler_user = "cobbler",
  $cobbler_password = "cobbler",

  $mco_pskey = "unset",
  $mco_stompuser = "mcollective",
  $mco_stomppassword = "marionette",

  $naily_version,
  $rabbitmq_naily_user = "naily",
  $rabbitmq_naily_password = "naily",

  $puppet_master_hostname = "${hostname}.${domain}",

  ) {

  Exec  {path => '/usr/bin:/bin:/usr/sbin:/sbin'}

  anchor { "nailgun-begin": }
  anchor { "nailgun-end": }

  Anchor<| title == "nailgun-begin" |> ->
  Class["nailgun::packages"] ->
  Class["nailgun::iptables"] ->
  Class["nailgun::nginx-repo"] ->
  Exec["start_nginx_repo"] ->
  Class["nailgun::user"] ->
  Class["nailgun::venv"] ->
  Class["nailgun::naily"] ->
  Class["nailgun::nginx-nailgun"] ->
  Class["nailgun::cobbler"] ->
  Class["nailgun::pm"] ->
  Class["nailgun::supervisor"] ->
  Anchor<| title == "nailgun-end" |>

  class { "nailgun::packages":
    gem_source => $gem_source,
  }

  class { "nailgun::iptables": }

  file { ["/etc/nginx/conf.d/default.conf",
          "/etc/nginx/conf.d/virtual.conf",
          "/etc/nginx/conf.d/ssl.conf"]:
    ensure => "absent",
    notify => Service["nginx"],
    before => Class["nailgun::nginx-repo"],
  }


  class { "nailgun::user":
    nailgun_group => $nailgun_group,
    nailgun_user => $nailgun_user,
  }

  class { "nailgun::venv":
    venv => $venv,
    venv_opts => "--system-site-packages",
    package => $package,
    version => $version,
    pip_opts => "${pip_index} ${pip_find_links}",
    nailgun_user => $nailgun_user,
    nailgun_group => $nailgun_group,
    databasefile => $databasefile,
    staticdir => $staticdir,
    templatedir => $templatedir,
    logfile => $logfile,
    rabbitmq_naily_user => $rabbitmq_naily_user,
    rabbitmq_naily_password => $rabbitmq_naily_password,
  }

  class {"nailgun::naily":
    rabbitmq_naily_user => $naily_user,
    rabbitmq_naily_password => $naily_password,
    version => $naily_version,
    gem_source => $gem_source,
  }

  class { "nailgun::supervisor":
    venv => $venv,
  }

  class { "nailgun::nginx-repo":
    repo_root => $repo_root,
    notify => Service["nginx"],
  }

  exec { "start_nginx_repo":
    command => "/etc/init.d/nginx start",
    unless => "/etc/init.d/nginx status | grep -q running",
  }

  class { "nailgun::nginx-nailgun":
    staticdir => $staticdir,
    notify => Service["nginx"],
  }

  class { "nailgun::cobbler":
    cobbler_user => "cobbler",
    cobbler_password => "cobbler",
    centos_iso => $centos_iso,
    centos_repos => $centos_repos,
  }

  class { "nailgun::pm":
    puppet_master_hostname => $puppet_master_hostname,
    gem_source => $gem_source,
  }

  class { "nailgun::mcollective":
    mco_pskey => $mco_pskey,
    mco_stompuser => $mco_stompuser,
    mco_stomppassword => $mco_stomppassword,
    rabbitmq_plugins_repo => "file:///var/www/rabbitmq-plugins",
  }

  rabbitmq_user { $rabbitmq_naily_user:
    admin     => true,
    password  => $rabbitmq_naily_password,
    provider  => 'rabbitmqctl',
    require   => Class['rabbitmq::server'],
  }

  rabbitmq_user_permissions { "${rabbitmq_naily_user}@/":
    configure_permission => '.*',
    write_permission     => '.*',
    read_permission      => '.*',
    provider             => 'rabbitmqctl',
    require              => Class['rabbitmq::server'],
  }

  class { "nailgun::nginx-service": }

}
