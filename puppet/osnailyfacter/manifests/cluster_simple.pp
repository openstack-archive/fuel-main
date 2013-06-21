class osnailyfacter::cluster_simple {

$network_config = {
  'vlan_start'     => $vlan_start,
}

$multi_host              = true
$quantum                 = false

$network_manager      = "nova.network.manager.${network_manager}"

$nova_hash     = parsejson($nova)
$mysql_hash    = parsejson($mysql)
$rabbit_hash   = parsejson($rabbit)
$glance_hash   = parsejson($glance)
$keystone_hash = parsejson($keystone)
$swift_hash    = parsejson($swift)
$cinder_hash   = parsejson($cinder)
$access_hash   = parsejson($access)
$extra_rsyslog_hash = parsejson($syslog)
$floating_hash = parsejson($floating_network_range)

if $auto_assign_floating_ip == 'true' {
  $bool_auto_assign_floating_ip = true
} else {
  $bool_auto_assign_floating_ip = false
}

$base_syslog_hash  = parsejson($base_syslog)
$base_syslog_rserver  = {
  'remote_type' => 'udp',
  'server' => $base_syslog_hash['syslog_server'],
  'port' => $base_syslog_hash['syslog_port']
}

$syslog_hash   = parsejson($syslog)
$syslog_rserver = {
  'remote_type' => $syslog_hash['syslog_transport'],
  'server' => $syslog_hash['syslog_server'],
  'port' => $syslog_hash['syslog_port'],
}

if $syslog_hash['syslog_server'] != "" and $syslog_hash['syslog_port'] != "" and $syslog_hash['syslog_transport'] != "" {
  $rservers = [$base_syslog_rserver, $syslog_rserver]
}
else {
  $rservers = [$base_syslog_rserver]
}

$rabbit_user   = 'nova'

$sql_connection           = "mysql://nova:${nova_hash[db_password]}@${controller_node_address}/nova"
$mirror_type = 'external'

$verbose = true
Exec { logoutput => true }

  case $role {
    "controller" : {
      include osnailyfacter::test_controller

      class { 'openstack::controller':
        admin_address           => $controller_node_address,
        public_address          => $controller_node_public,
        public_interface        => $public_interface,
        private_interface       => $fixed_interface,
        internal_address        => $controller_node_address,
        floating_range          => false,
        fixed_range             => $fixed_network_range,
        multi_host              => $multi_host,
        network_manager         => $network_manager,
        num_networks             => $num_networks,
        network_size            => $network_size,
        network_config          => $network_config,
        verbose                 => $verbose,
        auto_assign_floating_ip => $bool_auto_assign_floating_ip,
        mysql_root_password     => $mysql_hash[root_password],
        admin_email             => $access_hash[email],
        admin_user              => $access_hash[user],
        admin_password          => $access_hash[password],
        keystone_db_password    => $keystone_hash[db_password],
        keystone_admin_token    => $keystone_hash[admin_token],
        keystone_admin_tenant   => $access_hash[tenant],
        glance_db_password      => $glance_hash[db_password],
        glance_user_password    => $glance_hash[user_password],
        nova_db_password        => $nova_hash[db_password],
        nova_user_password      => $nova_hash[user_password],
        rabbit_password         => $rabbit_hash[password],
        rabbit_user             => $rabbit_user,
        export_resources        => false,
        quantum                 => $quantum,
        cinder                  => true,
        cinder_user_password    => $cinder_hash[user_password],
        cinder_db_password      => $cinder_hash[db_password],
        manage_volumes          => false,
        use_syslog              => true,
      }

      class { "::rsyslog::client":
        log_local => true,
        log_auth_local => true,
        rservers => $rservers,
      }

      nova_config { 'DEFAULT/start_guests_on_host_boot': value => $start_guests_on_host_boot }
      nova_config { 'DEFAULT/use_cow_images': value => $use_cow_images }
      nova_config { 'DEFAULT/compute_scheduler_driver': value => $compute_scheduler_driver }
      nova_config { 'DEFAULT/debug': value => 'true' }

      class { 'openstack::auth_file':
        admin_user           => $access_hash[user],
        admin_password       => $access_hash[password],
        keystone_admin_token => $keystone_hash[admin_token],
        admin_tenant         => $access_hash[tenant],
        controller_node      => $controller_node_address,
      }

      # glance_image is currently broken in fuel

      # glance_image {'testvm':
      #   ensure           => present,
      #   name             => "Cirros testvm",
      #   is_public        => 'yes',
      #   container_format => 'ovf',
      #   disk_format      => 'raw',
      #   source           => '/opt/vm/cirros-0.3.0-x86_64-disk.img',
      #   require          => Class[glance::api],
      # }

      class { 'openstack::img::cirros':
        os_username               => shellescape($access_hash[user]),
        os_password               => shellescape($access_hash[password]),
        os_tenant_name            => shellescape($access_hash[tenant]),
        img_name                  => "TestVM",
        stage                     => 'glance-image',
      }
      nova::manage::floating{$floating_hash:}
      Class[glance::api]        -> Class[openstack::img::cirros]
    }

    "compute" : {
      include osnailyfacter::test_compute

      class { 'openstack::compute':
        public_interface       => $public_interface,
        private_interface      => $fixed_interface,
        internal_address       => $internal_address,
        libvirt_type           => $libvirt_type,
        fixed_range            => $fixed_network_range,
        network_manager        => $network_manager,
        network_config         => $network_config,
        multi_host             => $multi_host,
        sql_connection         => $sql_connection,
        nova_user_password     => $nova_hash[user_password],
        rabbit_nodes           => [$controller_node_address],
        rabbit_password        => $rabbit_hash[password],
        rabbit_user            => $rabbit_user,
        auto_assign_floating_ip => $bool_auto_assign_floating_ip,
        glance_api_servers     => "${controller_node_address}:9292",
        vncproxy_host          => $controller_node_public,
        vnc_enabled            => true,
        #ssh_private_key        => 'puppet:///ssh_keys/openstack',
        #ssh_public_key         => 'puppet:///ssh_keys/openstack.pub',
        quantum                => $quantum,
        #quantum_host           => $quantum_host,
        #quantum_sql_connection => $quantum_sql_connection,
        #quantum_user_password  => $quantum_user_password,
        #tenant_network_type    => $tenant_network_type,
        service_endpoint       => $controller_node_address,
        cinder                 => true,
        cinder_user_password   => $cinder_hash[user_password],
        cinder_db_password     => $cinder_hash[db_password],
        manage_volumes         => false,
        db_host                => $controller_node_address,
        verbose                => $verbose,
        use_syslog             => true,
      }

      class { "::rsyslog::client":
        log_local => true,
        log_auth_local => true,
        rservers => $rservers,
      }

      nova_config { 'DEFAULT/start_guests_on_host_boot': value => $start_guests_on_host_boot }
      nova_config { 'DEFAULT/use_cow_images': value => $use_cow_images }
      nova_config { 'DEFAULT/compute_scheduler_driver': value => $compute_scheduler_driver }
      nova_config { 'DEFAULT/debug': value => 'true' }
    }

    "cinder" : {
      include keystone::python
      package { 'python-amqp':
        ensure => present
      }
      class { 'openstack::cinder':
        sql_connection       => "mysql://cinder:${cinder_hash[db_password]}@${controller_node_address}/cinder?charset=utf8",
        glance_api_servers   => "${controller_node_address}:9292",
        rabbit_password      => $rabbit_hash[password],
        rabbit_host          => false,
        rabbit_nodes         => [$controller_node_address],
        volume_group         => 'cinder',
        manage_volumes       => true,
        enabled              => true,
        auth_host            => $controller_node_address,
        iscsi_bind_host      => $storage_address,
        cinder_user_password => $cinder_hash[user_password],
        use_syslog           => true,
      }
      class { "::rsyslog::client":
        log_local => true,
        log_auth_local => true,
        rservers => $rservers,
      }
    }
  }
}
