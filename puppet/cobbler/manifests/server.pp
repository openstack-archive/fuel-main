class cobbler::server {
  include cobbler::packages
  
  Exec {
    path => '/usr/bin:/bin:/usr/sbin:/sbin'
  }

  case $operatingsystem {
    /(?i)(centos|redhat)/ : {
      $cobbler_service     = "cobblerd"
      $cobbler_web_service = "httpd"
      $dnsmasq_service     = "dnsmasq"

      service { "xinetd":
        enable     => true,
        ensure     => running,
        hasrestart => true,
        require    => Package[$cobbler::packages::cobbler_additional_packages],
      }

      file { "/etc/xinetd.conf":
        content => template("cobbler/xinetd.conf.erb"),
        owner   => root,
        group   => root,
        mode    => 0600,
        require => Package[$cobbler::packages::cobbler_additional_packages],
        notify  => Service["xinetd"],
      }

    }
    /(?i)(debian|ubuntu)/ : {
      $cobbler_service     = "cobbler"
      $cobbler_web_service = "apache2"
      $dnsmasq_service     = "dnsmasq"
      $apache_ssl_module   = "ssl"

    }
  }

  Service[$cobbler_service] -> Exec["cobbler_sync"] -> Service[$dnsmasq_service]

  service { $cobbler_service:
    enable     => true,
    ensure     => running,
    hasrestart => true,
    require    => Package[$cobbler::packages::cobbler_package],
  }

  service { $dnsmasq_service:
    enable     => true,
    ensure     => running,
    hasrestart => true,
    require    => Package[$cobbler::packages::dnsmasq_package],
    subscribe  => Exec["cobbler_sync"],
  }

  if $apache_ssl_module {
    file { '/etc/apache2/mods-enabled/ssl.load':
      ensure => link,
      target => '/etc/apache2/mods-available/ssl.load',
    } -> file { '/etc/apache2/mods-enabled/ssl.conf':
      ensure => link,
      target => '/etc/apache2/mods-available/ssl.conf',
    } -> file { '/etc/apache2/sites-enabled/default-ssl':
      ensure => link,
      target => '/etc/apache2/sites-available/default-ssl',
      before => Service[$cobbler_web_service],
      notify => Service[$cobbler_web_service],
    }
  }

  service { $cobbler_web_service:
    enable     => true,
    ensure     => running,
    hasrestart => true,
    require    => Package[$cobbler::packages::cobbler_web_package],
  }

  exec { "cobbler_sync":
    command     => "cobbler sync",
    refreshonly => true,
    require     => [
      Package[$cobbler::packages::cobbler_package],
      Package[$cobbler::packages::dnsmasq_package],],
    subscribe   => Service[$cobbler_service],
    notify      => Service[$dnsmasq_service],
    tries       => 20,
    try_sleep   => 3,
  }

  file { "/etc/cobbler/modules.conf":
    content => template("cobbler/modules.conf.erb"),
    owner   => root,
    group   => root,
    mode    => 0644,
    require => [Package[$cobbler::packages::cobbler_package],],
    notify  => [Service[$cobbler_service], Exec["cobbler_sync"],],
  }

  file { "/etc/cobbler/settings":
    content => template("cobbler/settings.erb"),
    owner   => root,
    group   => root,
    mode    => 0644,
    require => Package[$cobbler::packages::cobbler_package],
    notify  => [Service[$cobbler_service], Exec["cobbler_sync"],],
  }

  file { "/etc/cobbler/dnsmasq.template":
    content => template("cobbler/dnsmasq.template.erb"),
    owner   => root,
    group   => root,
    mode    => 0644,
    require => [
      Package[$cobbler::packages::cobbler_package],
      Package[$cobbler::packages::dnsmasq_package],],
    notify  => [
      Service[$cobbler_service],
      Exec["cobbler_sync"],
      Service[$dnsmasq_service],],
  }

  file { "/etc/cobbler/pxe/pxedefault.template":
    content => template("cobbler/pxedefault.template.erb"),
    owner   => root,
    group   => root,
    mode    => 0644,
    require => Package[$cobbler::packages::cobbler_package],
    notify  => [Service[$cobbler_service], Exec["cobbler_sync"],],
  }

  file { "/etc/cobbler/pxe/pxelocal.template":
    content => template("cobbler/pxelocal.template.erb"),
    owner   => root,
    group   => root,
    mode    => 0644,
    require => Package[$cobbler::packages::cobbler_package],
    notify  => [Service[$cobbler_service], Exec["cobbler_sync"],],
  }

  exec { "/var/lib/tftpboot/chain.c32":
    command => "cp /usr/share/syslinux/chain.c32 /var/lib/tftpboot/chain.c32",
    unless  => "test -e /var/lib/tftpboot/chain.c32",
    require => [
      Package[$cobbler::packages::cobbler_additional_packages],
      Package[$cobbler::packages::cobbler_package],]
  }
}
