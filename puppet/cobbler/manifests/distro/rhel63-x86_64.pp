#
# This class is intended to make cobbler distro rhel63-x86_64. It will 
# download and mount rhel ISO image.
#
# [http_iso] This is the url from where to download rhel 6.3 ISO image.
# This ISO image is needed to mount it and use its vmlinuz and initrd.img files.
# If it also contains RPM packages including ruby, wget and so on, then you
# can install system completely from this ISO image.

# [ks_url] This is the url of RPM repository from where to install system.
# This will be used as the url parameter in kickstart file. You can also
# use here the key word 'cobbler' in order to use mounted ISO image as main
# repository.


class cobbler::distro::rhel63-x86_64(
  $http_iso = "http://10.0.0.1/~hex/iso/rhel-server-6.3-x86_64-boot.iso",
  $ks_url   = "http://10.0.0.1/~hex/rhel/6.3/os/x86_64"
  ) {

  Exec {path => '/usr/bin:/bin:/usr/sbin:/sbin'}

  $ks_mirror = '/var/www/cobbler/ks_mirror'

  # rhel-server-6.3-x86_64-boot
  $iso_name = extension_basename($http_iso, "true")
  # rhel-server-6.3-x86_64-boot.iso
  $iso_basename = extension_basename($http_iso) 
  # /var/www/cobbler/ks_mirror/rhel-server-6.3-x86_64-boot.iso
  $iso = "${ks_mirror}/${iso_basename}"
  # /var/www/cobbler/ks_mirror/rhel-server-6.3-x86_64-boot
  $iso_mnt = "${ks_mirror}/${iso_name}"
  # /var/www/cobbler/links/rhel-server-6.3-x86_64-boot
  $iso_link = "/var/www/cobbler/links/$iso_name"

  if $ks_url == "cobbler" {
    $tree = "http://@@server@@/cblr/links/${iso_name}"
  }
  else {
    $tree = $ks_url
  }
  
  file { $iso_mnt:
    ensure => directory,
    owner => root,
    group => root,
    mode => 0555,
  }

  # HERE IS ASSUMED THAT wget PACKAGE INSTALLED AS WE NEED IT
  # TO DOWNLOAD RHEL ISO IMAGE

  exec { "wget ${http_iso}":
    command => "wget -q -O- ${http_iso} > ${iso}",
    onlyif => "test ! -s ${iso}",
    timeout => 0,
  }

  mount { $iso_mnt:
    device => $iso,
    options => "loop",
    fstype => "iso9660",
    ensure => mounted,
    require => [Exec["wget ${http_iso}"], File[$iso_mnt]],
  }

  file { $iso_link:
    ensure => link,
    target => $iso_mnt,
  }

  
  cobbler_distro { "rhel63-x86_64":
    kernel => "${iso_mnt}/isolinux/vmlinuz",
    initrd => "${iso_mnt}/isolinux/initrd.img",
    arch => "x86_64",
    breed => "redhat",
    osversion => "rhel6",
    ksmeta => "tree=${tree}",
    require => Mount[$iso_mnt],
  }
}
