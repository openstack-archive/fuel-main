class cobbler::distro::ubuntu_1204_x86_64(
  $http_iso = 'http://archive.ubuntu.com/ubuntu/dists/precise/main/installer-amd64/current/images/netboot/mini.iso',
  $ks_url   = 'http://us.archive.ubuntu.com/ubuntu',
  ){

  Exec {path => '/usr/bin:/bin:/usr/sbin:/sbin'}

  case $::operatingsystem {
    /(?i)(centos|redhat)/:  {
      $ks_mirror = '/var/www/cobbler/ks_mirror'
    }
    /(?i)(debian|ubuntu)/:  {
      $ks_mirror = '/usr/share/cobbler/webroot/cobbler/ks_mirror'
    }
  }

  # mini
  $iso_name = extension_basename($http_iso, 'true')
  # mini.iso
  $iso_basename = extension_basename($http_iso)
  # /var/www/cobbler/ks_mirror/ubuntu-12.04-x86_64-mini.iso
  $iso = "${ks_mirror}/ubuntu-12.04-x86_64-${iso_basename}"
  # /var/www/cobbler/ks_mirror/ubuntu-12.04-x86_64-mini
  $iso_mnt = "${ks_mirror}/ubuntu-12.04-x86_64-${iso_name}"
  # /var/www/cobbler/links/ubuntu-12.04-x86_64-mini
  $iso_link = "/var/www/cobbler/links/${iso_name}"

  if $ks_url == 'cobbler' {
    $tree_host = "@@server@@"
    $tree_url = "/cblr/links/${iso_name}"
  }
  else {
    $tree_host = inline_template("<%= @ks_url.split('http://')[1].split('/')[0] %>")
    $tree_url = inline_template("/<%= @ks_url.split('http://')[1].split('/')[1 .. -1].join('/') %>")
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

  cobbler_distro { "ubuntu_1204_x86_64":
    kernel    => "${iso_mnt}/linux",
    initrd    => "${iso_mnt}/initrd.gz",
    arch      => 'x86_64',
    breed     => 'ubuntu',
    osversion => 'precise',
    ksmeta    => "tree_host=${tree_host} tree_url=${tree_url}",
    require   => Mount[$iso_mnt],
  }


  }
