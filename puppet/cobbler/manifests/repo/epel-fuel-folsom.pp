#
# This class is intended to make cobbler repo epel-fuel-folsom. It will
# download necessary epel and fuel packages for epel-fuel-folsom repo.
#
# [mirror_type] This is the url from where to download epel-fuel-folsom repo.


class cobbler::repo::epel-fuel-folsom(
    $mirror_type = 'external',
  ) {
  $mirrorlist="http://download.mirantis.com/epel-fuel-folsom/mirror.${mirror_type}.list"


  Exec {path => '/usr/bin:/bin:/usr/sbin:/sbin'}


  cobbler_repo { 'epel-fuel-folsom':
    name      => "epel-fuel-folsom",
    arch      => "x86_64",
    breed     => "yum",
    comment   => "EPEL Fuel Folsom",
    keepupdated => "Y",
    mirrorlist => $mirrorlist,
    mirrorlocally => "Y",
    ensure    => present,
  }
}

