$openstack_version = {
  'keystone'   => 'latest',
  'glance'     => 'latest',
  'horizon'    => 'latest',
  'nova'       => 'latest',
  'novncproxy' => 'latest',
  'cinder'     => 'latest',
}

tag("${deployment_id}::${::environment}")

stage {'netconfig':
  before => Stage['main'],
}

stage {'openstack-firewall':
  before  => Stage['main'],
  require => Stage['netconfig'],
}

stage {'glance-image':
  require => Stage['main'],
}

node default {
  case $deployment_mode {
    "singlenode": { include osnailyfacter::cluster_simple }
    "multinode": { include osnailyfacter::cluster_simple }
    "ha": { include osnailyfacter::cluster_ha }
  }

  class {'osnailyfacter::network_setup': stage => 'netconfig'}
  class {'openstack::firewall': stage => 'openstack-firewall'}

  # Workaround for fuel bug with firewall
  firewall {'003 remote rabbitmq ':
    sport   => [ 4369, 5672, 41055, 55672, 61613 ],
    proto   => 'tcp',
    action  => 'accept',
    require => Class['openstack::firewall'],
  }
}
