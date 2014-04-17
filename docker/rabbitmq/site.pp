$fuel_settings = parseyaml($astute_settings_yaml)
$fuel_version = parseyaml($fuel_version_yaml)

$management_port = "55672"
$stompport = "61613"
$stomp = false
$vhost = "mcollective"

# naily
$rabbitmq_astute_user = "naily"
$rabbitmq_astute_password = "naily"

#mcollective
$user = "mcollective"
$password = "marionette"

if $stomp {
  $actual_vhost = "/"
} else {
  rabbitmq_vhost { $vhost: }
  $actual_vhost = $vhost
}

class { 'rabbitmq::server':
  service_ensure     => running,
  delete_guest_user  => true,
  config_cluster     => false,
  cluster_disk_nodes => [],
  config_stomp       => true,
  stomp_port         => $stompport,
  node_ip_address    => 'UNSET',
}

  
#ulimit disabling
file { "/etc/default/rabbitmq-server":
  ensure  => absent,
  require => Package["rabbitmq-server"],
  before  => Service["rabbitmq-server"],
}

file { "/var/log/rabbitmq":
  ensure  => directory,
  owner   => 'rabbitmq',
  group   => 'rabbitmq',
  mode    => 0755,
  require => Package["rabbitmq-server"],
  before  => Service["rabbitmq-server"],
}

file { "/etc/rabbitmq/enabled_plugins":
  content => template("mcollective/enabled_plugins.erb"),
  owner   => root,
  group   => root,
  mode    => 0644,
  require => Package["rabbitmq-server"],
  notify  => Service["rabbitmq-server"],
}

rabbitmq_user { $rabbitmq_astute_user:
  admin     => true,
  password  => $rabbitmq_astute_password,
  provider  => 'rabbitmqctl',
  require   => Class['rabbitmq::server'],
}

rabbitmq_user_permissions { "${rabbitmq_astute_user}@/":
  configure_permission => '.*',
  write_permission     => '.*',
  read_permission      => '.*',
  provider             => 'rabbitmqctl',
  require              => Class['rabbitmq::server'],
}

rabbitmq_user { $user:
  admin    => true,
  password => $password,
  provider => 'rabbitmqctl',
  require  => Class['rabbitmq::server'],
}

rabbitmq_user_permissions { "${user}@${actual_vhost}":
  configure_permission => '.*',
  write_permission     => '.*',
  read_permission      => '.*',
  provider             => 'rabbitmqctl',
  require              => [Class['rabbitmq::server'], Rabbitmq_user[$user],]
}

exec { 'create-mcollective-directed-exchange':
  command   => "curl -i -u ${user}:${password} -H \"content-type:application/json\" -XPUT \
    -d'{\"type\":\"direct\",\"durable\":true}' http://localhost:${management_port}/api/exchanges/${actual_vhost}/mcollective_directed",
  logoutput => true,
  require   => [Service['rabbitmq-server'], Rabbitmq_user_permissions["${user}@${actual_vhost}"]],
  path      => '/bin:/usr/bin:/sbin:/usr/sbin',
  tries     => 10,
  try_sleep => 3,
}

exec { 'create-mcollective-broadcast-exchange':
  command   => "curl -i -u ${user}:${password} -H \"content-type:application/json\" -XPUT \
    -d'{\"type\":\"topic\",\"durable\":true}' http://localhost:${management_port}/api/exchanges/${actual_vhost}/mcollective_broadcast",
  logoutput => true,
  require   => [Service['rabbitmq-server'], Rabbitmq_user_permissions["${user}@${actual_vhost}"]],
  path      => '/bin:/usr/bin:/sbin:/usr/sbin',
  tries     => 10,
  try_sleep => 3,
}
