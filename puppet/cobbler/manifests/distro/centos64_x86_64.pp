# 
# This class is intended to make cobbler distro centos64_x86_64. It will
# download and mount centos ISO image.
#
# [http_iso] This is the url from where to download centos 6.4 ISO image.
# This ISO image is needed to mount it and use its vmlinuz and initrd.img files.
# If it also contains RPM packages including ruby, wget and so on, then you
# can install system completely from this ISO image.

# [ks_url] This is the url of RPM repository from where to install system.
# This will be used as the url parameter in kickstart file. You can also
# use here the key word 'cobbler' in order to use mounted ISO image as main
# repository.


class cobbler::distro::centos64_x86_64(
  $http_iso = 'http://download.mirantis.com/epel-fuel-grizzly/isos/x86_64/CentOS-6.4-x86_64-minimal.iso',
  $ks_url   = 'http://download.mirantis.com/epel-fuel-grizzly'
  ) {

  Exec {path => '/usr/bin:/bin:/usr/sbin:/sbin'}

  case $::operatingsystem {
    /(?i)(centos|redhat)/:  {
      $ks_mirror = '/var/www/cobbler/ks_mirror'
    }
    /(?i)(debian|ubuntu)/:  {
      $ks_mirror = '/usr/share/cobbler/webroot/cobbler/ks_mirror'
    }
  }

  # CentOS-6.4-x86_64-minimal
  $iso_name = extension_basename($http_iso, 'true')
  # CentOS-6.4-x86_64-minimal.iso
  $iso_basename = extension_basename($http_iso)
  # /var/www/cobbler/ks_mirror/CentOS-6.4-x86_64-minimal.iso
  $iso = "${ks_mirror}/${iso_basename}"
  # /var/www/cobbler/ks_mirror/CentOS-6.4-x86_64-minimal
  $iso_mnt = "${ks_mirror}/${iso_name}"
  # /var/www/cobbler/links/CentOS-6.4-x86_64-minimal
  $iso_link = "/var/www/cobbler/links/${iso_name}"

  if $ks_url == 'cobbler' {
    $tree = "http://@@server@@/cblr/links/${iso_name}"
  }
  else {
    $tree = $ks_url
  }

  file { $iso_mnt:
    ensure => directory,
  }

  if $http_iso =~ /^http:\/\/.+/ {
    # HERE IS ASSUMED THAT wget PACKAGE INSTALLED AS WE NEED IT
    # TO DOWNLOAD CENTOS ISO IMAGE
    exec { "get ${http_iso}":
      command => "wget -q -O- ${http_iso} > ${iso}",
      timeout => 0,
      onlyif  => "test ! -s ${iso}",
    }
  }
  elsif $http_iso =~ /^file:\/\/.+/ {
    $http_iso_path = split($http_iso, 'file://')
    exec { "get ${http_iso}":
      command => "cp ${http_iso_path[1]} ${iso}",
      onlyif  => "test ! -s ${iso}",
    }
  }

  mount { $iso_mnt:
    ensure  => mounted,
    device  => $iso,
    options => 'loop',
    fstype  => 'iso9660',
    require => [Exec["get ${http_iso}"], File[$iso_mnt]],
  }

  file { $iso_link:
    ensure => link,
    target => $iso_mnt,
  }

  cobbler_distro { 'centos64_x86_64':
    kernel    => "${iso_mnt}/isolinux/vmlinuz",
    initrd    => "${iso_mnt}/isolinux/initrd.img",
    arch      => 'x86_64',
    breed     => 'redhat',
    osversion => 'rhel6',
    ksmeta    => "tree=${tree}",
    require   => Mount[$iso_mnt],
  }
}
