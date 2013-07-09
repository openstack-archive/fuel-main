#
# This class is intended to make cobbler profile ubuntu_1204_x86_64.
#
# [distro] The name of cobbler distro to bind profile to.
#
# [ks_system_timezone] System timezone on installed system.
#
# [ks_encrypted_root_password] Hash of the root password on installed system.

class cobbler::profile::ubuntu_1204_x86_64(
  $distro  = "ubuntu_1204_x86_64",
  $ks_repo = [
    {
      "name" => "Puppet",
      "url"  => "http://apt.puppetlabs.com/",
      "key"  => "http://apt.puppetlabs.com/pubkey.gpg",
      "release" => "precise",
      "repos" => "main dependencies",
    },
  ],

  $ks_system_timezone = "America/Los_Angeles",

  # default password is 'r00tme'
  $ks_encrypted_root_password = "\$6\$tCD3X7ji\$1urw6qEMDkVxOkD33b4TpQAjRiCeDZx0jmgMhDYhfB9KuGfqO9OcMaKyUxnGGWslEDQ4HxTw7vcAMP85NxQe61",

  $kopts = "priority=critical locale=en_US netcfg/choose_interface=auto auto=true",
  ){

  case $operatingsystem {
    /(?i)(ubuntu|debian|centos|redhat)$/:  {
      $ks_dir = "/var/lib/cobbler/kickstarts"
    }
  }

  file { "${ks_dir}/ubuntu_1204_x86_64.preseed":
    content => template("cobbler/preseed/ubuntu-1204.preseed.erb"),
    owner => root,
    group => root,
    mode => 0644,
  } ->

  cobbler_profile { "ubuntu_1204_x86_64":
    kickstart => "${ks_dir}/ubuntu_1204_x86_64.preseed",
    kopts => $kopts,
    distro => $distro,
    ksmeta => "",
    menu => true,
  }

  }
