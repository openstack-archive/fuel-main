class cobbler::packages {

  case $operatingsystem {
    /(?i)(centos|redhat)/:  {
      $cobbler_package = "cobbler"
      $cobbler_version = "2.2.3-2.el6"
      $cobbler_web_package = "cobbler-web"
      $cobbler_web_package_version = "2.2.3-2.el6"
      $dnsmasq_package = "dnsmasq"
      $cobbler_additional_packages = ["xinetd", "tftp-server", "syslinux", "wget", "python-ipaddr"]
      $django_package = "Django"
      $django_version = "1.3.4-1.el6"
    }
    /(?i)(debian|ubuntu)/:  {
      $cobbler_package = "cobbler"
      $cobbler_version = "2.2.2-0ubuntu33.2"
      $cobbler_web_package = "cobbler-web"
      $cobbler_web_package_version = "2.2.2-0ubuntu33.2"
      $dnsmasq_package = "dnsmasq"
      $cobbler_additional_packages = ["tftpd-hpa", "syslinux", "wget", "python-ipaddr"]
      $django_package = "python-django"
      $django_version = "1.3.1-4ubuntu1"
    }
  }

  define cobbler_safe_package(){
    if ! defined(Package[$name]){
      @package { $name : }
    }
  }

  cobbler_safe_package { $cobbler_additional_packages : }

  package { $django_package :
        ensure => $django_version
  }

  package { $cobbler_package :
    ensure => $cobbler_version,
    require => [
                Package[$dnsmasq_package],
                Package[$cobbler_additional_packages],
                Package[$django_package],
                ],
  }

  package { $cobbler_web_package :
    ensure => $cobbler_web_package_version,
    require => Package[$cobbler_package]
  }

  package { $dnsmasq_package:
    ensure => installed
  }

  Package<||>

}
