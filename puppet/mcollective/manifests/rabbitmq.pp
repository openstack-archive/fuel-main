class mcollective::rabbitmq(
  $user     = "mcollective",
  $password = "mcollective",
  $stompport = "61613",
  $management_port = "55672",
  $stomp = false,
  $vhost = "mcollective",
  ){

  define mcollective_rabbitmq_safe_package(){
    if ! defined(Package[$name]){
      @package { $name : }
    }
  }

  define access_to_rabbitmq_port($port, $protocol='tcp') {
    $rule = "-p $protocol -m state --state NEW -m $protocol --dport $port -j ACCEPT"
    exec { "access_to_cobbler_${protocol}_port: $port":
      command => "iptables -t filter -I INPUT 1 $rule; \
        /etc/init.d/iptables save",
      unless => "iptables -t filter -S INPUT | grep -q \"^-A INPUT $rule\"",
      path => '/bin:/usr/bin:/sbin:/usr/sbin',
    }
  }

  file {"/etc/rabbitmq/enabled_plugins":
    content => template("mcollective/enabled_plugins.erb"),
    owner => root,
    group => root,
    mode => 0644,
  }

  access_to_rabbitmq_port { "${stompport}_tcp": port => $stompport }

  class { 'rabbitmq::server':
    service_ensure     => 'running',
    delete_guest_user  => true,
    config_cluster     => false,
    cluster_disk_nodes => [],
    config_stomp       => true,
    stomp_port         => $stompport,
  }

  if $stomp {
    $actual_vhost = "/"
  }
  else {
    rabbitmq_vhost { $vhost : }
    $actual_vhost = $vhost
  }

  rabbitmq_user { $user:
    admin     => true,
    password  => $password,
    provider  => 'rabbitmqctl',
    require   => Class['rabbitmq::server'],
  }

  rabbitmq_user_permissions { "${user}@${actual_vhost}":
    configure_permission => '.*',
    write_permission     => '.*',
    read_permission      => '.*',
    provider             => 'rabbitmqctl',
    require              => [
                             Class['rabbitmq::server'],
                             Rabbitmq_user[$user],
                             ]
  }

  exec { 'create-mcollective-directed-exchange':
    command => "curl -i -u ${user}:${password} -H \"content-type:application/json\" -XPUT \
      -d'{\"type\":\"direct\",\"durable\":true}' http://localhost:${management_port}/api/exchanges/${actual_vhost}/mcollective_directed",
    logoutput => true,
    require => [Service['rabbitmq-server'], Rabbitmq_user_permissions["${user}@${actual_vhost}"]],
    path => '/bin:/usr/bin:/sbin:/usr/sbin',
  }

  exec { 'create-mcollective-broadcast-exchange':
    command => "curl -i -u ${user}:${password} -H \"content-type:application/json\" -XPUT \
      -d'{\"type\":\"topic\",\"durable\":true}' http://localhost:${management_port}/api/exchanges/${actual_vhost}/mcollective_broadcast",
    logoutput => true,
    require => [Service['rabbitmq-server'], Rabbitmq_user_permissions["${user}@${actual_vhost}"]],
    path => '/bin:/usr/bin:/sbin:/usr/sbin',
  }

}
