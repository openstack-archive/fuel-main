class rpmcache ( $releasever, $pkgdir, $numtries,
$rh_username, $rh_password, $rh_base_channels, $rh_openstack_channel,
$use_satellite = false, $sat_hostname = false, $activation_key = false, $sat_base_channels, $sat_openstack_channel)  {

  Exec  {path => '/usr/bin:/bin:/usr/sbin:/sbin'}
  package { "yum-utils":
    ensure => "latest"
  } ->
  package { "subscription-manager":
    ensure => "latest"
  } ->

  file { '/etc/pki/product':
    ensure => directory,
  } ->
  file { '/etc/pki/product/69.pem':
    ensure => present,
    source => 'puppet:///modules/rpmcache/69.pem',
    owner => 'root',
    group => 'root',
    mode => 0644,
  } ->

  file { '/etc/pki/product/191.pem':
    ensure => present,
    source => 'puppet:///modules/rpmcache/191.pem',
    owner => 'root',
    group => 'root',
    mode => 0644,
  } ->

  file { '/etc/pki/rpm-gpg/RPM-GPG-KEY-redhat-release':
    ensure => present,
    source => 'puppet:///modules/rpmcache/RPM-GPG-KEY-redhat-release',
    owner => 'root',
    group => 'root',
    mode => 0644,
  } ->

  file { '/etc/nailgun/':
    ensure => directory,
    owner => 'root',
    group => 'root',
    mode => '0755'
  } ->
  file { '/etc/nailgun/required-rpms.txt':
    ensure => present,
    source => 'puppet:///modules/rpmcache/required-rpms.txt',
    owner => 'root',
    group => 'root',
    mode => 0644,
    require => File['/etc/nailgun/']
  } ->
  file { '/usr/local/bin':
    ensure => directory,
  } ->

  file { '/usr/local/bin/repotrack':
    ensure => present,
    source => 'puppet:///modules/rpmcache/repotrack',
    owner => 'root',
    group => 'root',
    mode => 0755,
  } ->

  file { '/usr/sbin/build_rpm_cache':
    content => template('rpmcache/build_rpm_cache.erb'),
    owner => 'root',
    group => 'root',
    mode => 0755,
  } ->
  exec { 'build_rpm_cache':
    command => '/usr/sbin/build_rpm_cache',
    require => File['/usr/sbin/build_rpm_cache'],
    logoutput => true,
    timeout => 0
  } ->
  cobbler_distro { "rhel-x86_64":
    kernel => "${pkgdir}/isolinux/vmlinuz",
    initrd => "${pkgdir}/isolinux/initrd.img",
    arch => "x86_64",
    breed => "redhat",
    osversion => "rhel6",
    ksmeta => "tree=http://@@server@@:8080/rhel",
  } ->

  cobbler_profile { "rhel-x86_64":
    kickstart => "/var/lib/cobbler/kickstarts/centos-x86_64.ks",
    kopts => "",
    distro => "rhel-x86_64",
    ksmeta => "redhat_register_user=${rh_username} redhat_register_password=${rh_password} redhat_management_type=cert",
    menu => true,
    require => Cobbler_distro["rhel-x86_64"],
  } ->
  exec {'rebuild-fuel-repo':
    command => "/bin/cp /var/www/nailgun/centos/fuelweb/x86_64/repodata/comps.xml ${pkgdir}/repodata/comps.xml; /usr/bin/createrepo -g ${pkgdir}/repodata/comps.xml ${pkgdir}",
  }->
  exec {'check-rpm':
    command   => "/bin/find ${pkgdir} -name '*.rpm' | /usr/bin/xargs /bin/rpm --checksig | grep 'MD5 NOT OK'",
    logoutput => true,
    returns   => 1,
  }
  $hack_packages = [
    'xinetd-2.3.14-38.el6.x86_64.rpm',
    'xfsprogs-3.1.1-10.el6.x86_64.rpm',
    'qpid-cpp-server-cluster-0.14-22.el6_3.x86_64.rpm',
    'qpid-cpp-server-store-0.14-22.el6_3.x86_64.rpm',
    'qpid-tests-0.14-1.el6_2.noarch.rpm',
    'qpid-tools-0.14-6.el6_3.noarch.rpm',
    'qpid-cpp-server-ssl-0.14-22.el6_3.x86_64.rpm',
  ]
  define get_hack_package (
    $base_url="http://mirror.yandex.ru/centos/6.4/os/x86_64/Packages/",
    $pkgdir=$pkgdir,
  ) {
    exec {"Download_${name}":
      command   => "/bin/mkdir -p ${pkgdir}/fuel/Packages; /usr/bin/wget -c -P ${pkgdir}/fuel/Packages ${base_url}/${name}",
      logoutput => true,
      before    => Exec['rebuild-fuel-repo'],
    }
  }
  get_hack_package{$hack_packages:}

  file { '/etc/nailgun/req-fuel-rhel.txt':
    ensure => present,
    source => 'puppet:///modules/rpmcache/req-fuel-rhel.txt',
    owner => 'root',
    group => 'root',
    mode => 0644,
    require => File['/etc/nailgun/']
  } ->
  exec {'fuel-rpms':
    command => "/bin/mkdir -p ${pkgdir}/fuel/Packages; /bin/cat /etc/nailgun/req-fuel-rhel.txt | /usr/bin/xargs -n 1 -I xxx /bin/cp /var/www/nailgun/centos/fuelweb/x86_64/Packages/xxx /var/www/nailgun/rhel/fuel/Packages/",
    logoutput => true,
    before    => Exec['rebuild-fuel-repo'],
  }
}
