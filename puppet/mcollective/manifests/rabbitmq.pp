class mcollective::rabbitmq(
  $user     = "mcollective",
  $password = "mcollective",
  $stompport     = "61613",
  $port = "5672",
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
      unless => "iptables -t filter -S INPUT | grep -q \"^-A INPUT $rule\""
    }
  }


  if $stomp {
    access_to_rabbimq_port { "${stompport}_tcp": port => $stompport }

    class { 'rabbitmq::server':
      service_ensure     => 'running',
      delete_guest_user  => true,
      config_cluster     => false,
      cluster_disk_nodes => [],
      config_stomp       => true,
      stomp_port         => $stompport,
    }

    file {"/etc/rabbitmq/enabled_plugins":
      content => template("mcollective/enabled_plugins.erb"),
      owner => root,
      group => root,
      mode => 0644,
      require => Package["rabbitmq-server"],
      notify => Service["rabbitmq-server"],
    }

    $actualvhost = "/"
  }
  else {
    access_to_rabbimq_port { "${port}_tcp": port => $port }

    class { 'rabbitmq::server':
      service_ensure     => 'running',
      delete_guest_user  => true,
      config_cluster     => false,
      cluster_disk_nodes => [],
      config_stomp       => true,
      stomp_port         => $stompport,
    }

    rabbitmq_vhost { $vhost : }
    $actual_vhost = $vhost
  }

  rabbitmq_user { $user:
    admin     => true,
    password  => $password,
    provider  => 'rabbitmqctl',
    require   => Class['rabbitmq::server'],
  }

  rabbitmq_user_permissions { "${user}@${actualvhost}":
    configure_permission => '.*',
    write_permission     => '.*',
    read_permission      => '.*',
    provider             => 'rabbitmqctl',
    require              => [
                             Class['rabbitmq::server'],
                             Rabbitmq_user[$user],
                             ]
  }

  }
