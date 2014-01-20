# = Класс: acpid
#
# Простой класс, который устанавливает и запускает службу acpid
#
# == Параметры
#
# [*status*] Запустить ли службу? [true, false]
#
class acpid($status = true) {

  if ($::osfamily == 'Debian') {
    $package = 'acpid'
    $service = 'acpid'
  }
  elsif ($::osfamily == 'RedHat') {
    $package = 'acpid'
    $service = 'acpid'
  }
  else {
    fail("Module ${module_name} is not supported on ${::operatingsystem}!")
  }

  if ($status) {
    $ensure = 'running'
    $enable = true
  }
  else {
    $ensure = 'stopped'
    $enable = false
  }

  package { $package :
    ensure => installed,
  }

  service { $service :
    ensure     => $ensure,
    enable     => $enable,
    hasrestart => true,
    hasstatus  => true,
  }

  Package[$package] -> Service[$service]

}
