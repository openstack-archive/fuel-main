class mcollective::rabbitmq(
  $stompuser     = "mcollective",
  $stomppassword = "mcollective",
  $stompport     = "61613",
  ){

  define mcollective_rabbitmq_safe_package(){
    if ! defined(Package[$name]){
      @package { $name : }
    }
  }
  
  define access_to_stomp_port($port, $protocol='tcp') {
    $rule = "-p $protocol -m state --state NEW -m $protocol --dport $port -j ACCEPT"
    exec { "access_to_cobbler_${protocol}_port: $port": 
      command => "iptables -t filter -I INPUT 1 $rule; \
      /etc/init.d/iptables save",
      unless => "iptables -t filter -S INPUT | grep -q \"^-A INPUT $rule\""
    }
  }

  access_to_stomp_port { "${stompport}_tcp": port => $stompport }


  class { 'rabbitmq::server':
    service_ensure     => 'running',
    delete_guest_user  => true,
    config_cluster     => false,
    cluster_disk_nodes => [],
    config_stomp       => true,
    stomp_port         => $stompport,
  }
        
  rabbitmq_user { $stompuser:
    admin     => true,
    password  => $stomppassword,
    provider  => 'rabbitmqctl',
    require   => Class['rabbitmq::server'],
  }
  
  rabbitmq_user_permissions { "${stompuser}@/":
    configure_permission => '.*',
    write_permission     => '.*',
    read_permission      => '.*',
    provider             => 'rabbitmqctl',
    require              => Class['rabbitmq::server'],
  }
    
  # TODO
  # IMPLEMENT RABBITMQ PLUGIN TYPE IN rabbitmq MODULE
  
  file {"/etc/rabbitmq/enabled_plugins":
    content => template("mcollective/enabled_plugins.erb"),
    owner => root,
    group => root,
    mode => 0644,
    require => Package["rabbitmq-server"],
    notify => Service["rabbitmq-server"],
  }

  # IT SEEMS THERE IS NO PACKAGED RABBITMQ PLUGINS
  # FOR REDHAT BASED OS AND EVEN rabbitmq-plugins BINARY IS NOT INSTALLED.
  # SO WE NEED TO INSTALL NEEDED PLUGINS BY HAND
  # IT MUST BE IMPROVED IN FUTURE BY IMPLEMETING CORRESPONDING PUPPET TYPE

  file {"/root/install_rabbitmq_plugin.sh":
    content => template("mcollective/install_rabbitmq_plugin.sh.erb"),
    owner => root,
    group => root,
    mode => 0755,
  }

  # IT IS NEEDED IN ORDER TO DOWNLOAD RABBITMQ PLUGINS
  mcollective_rabbitmq_safe_package{ "wget": }
  
  define mco_install_rabbitmq_plugin() {
    exec {"mco_install_rabbitmq_plugin_${name}":
      command => "/root/install_rabbitmq_plugin.sh ${name} install",
      unless => "/root/install_rabbitmq_plugin.sh ${name} is_installed",
      require => [
                  File["/root/install_rabbitmq_plugin.sh"],
                  Package['rabbitmq-server'],
                  ],
    }
  }

  mco_install_rabbitmq_plugin{"rabbitmq_stomp":}
  mco_install_rabbitmq_plugin{"amqp_client":}

  Package<| title == wget |> -> 
  Mco_install_rabbitmq_plugin<||> ->
  File<| title == "/etc/rabbitmq/enabled_plugins" |>

  }
