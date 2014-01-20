# = Класс: ntp
#
# Демонстрационный класс, который устанавливает пакет ntp,
# создаёт конфигурационный файл и запускает службу ntp.
#
class ntp {
  if $::osfamily == 'RedHat' {
    $package   = 'ntp'
    $service   = 'ntpd'
    $config    = '/etc/ntp.conf'
    $conf_from = 'centos-ntp.conf'
  } elsif $::osfamily == 'Debian' {
    $package   = 'ntp'
    $service   = 'ntp'
    $config    = '/etc/ntp.conf'
    $conf_from = 'ubuntu-ntp.conf'
  }
  else {
    fail("Module ${module_name} is not supported on ${::operatingsystem}!")
  }

  package { $package :
    ensure => installed,
  }

  file { $config :
    ensure => present,
    owner  => 'root',
    group  => 'root',
    mode   => '0644',
    source => "puppet:///modules/ntp/${conf_from}",
  }

  service { $service :
    ensure     => 'running',
    enable     => true,
    hasrestart => true,
    hasstatus  => true,
  }

  Package[$package] -> File[$config] ~> Service[$service]

}
