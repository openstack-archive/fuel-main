class osnailyfacter::cluster_simple {

if $network_manager == 'VlanManager' {
  $private_interface = $vlan_interface
}else{
  $private_interface = $fixed_interface
}
$network_config = {
  'vlan_start'     => $vlan_start,
}

$cinder                  = false
$multi_host              = true
$manage_volumes          = false
$quantum                 = false

$network_manager      = "nova.network.manager.${network_manager}"

$nova_hash     = parsejson($nova)
$mysql_hash    = parsejson($mysql)
$rabbit_hash   = parsejson($rabbit)
$glance_hash   = parsejson($glance)
$keystone_hash = parsejson($keystone)
$swift_hash    = parsejson($swift)
$access_hash    = parsejson($access)

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
        private_interface       => $private_interface,
        internal_address        => $controller_node_address,
        floating_range          => $floating_network_range,
        fixed_range             => $fixed_network_range,
        multi_host              => $multi_host,
        network_manager         => $network_manager,
        num_networks             => $num_networks,
        network_size            => $network_size,
        network_config          => $network_config,
        verbose                 => $verbose,
        auto_assign_floating_ip => $auto_assign_floating_ip,
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
        cinder                  => $cinder,
        manage_volumes          => $manage_volumes,
        nv_physical_volume      => $nv_physical_volume,
      }
      nova_config { 'DEFAULT/start_guests_on_host_boot': value => $start_guests_on_host_boot }
      nova_config { 'DEFAULT/use_cow_images': value => $use_cow_images }
      nova_config { 'DEFAULT/compute_scheduler_driver': value => $compute_scheduler_driver }

      class { 'openstack::auth_file':
        admin_user           => $access_hash[user],
        admin_password       => $access_hash[password],
        keystone_admin_token => $keystone_hash[admin_token],
        admin_tenant         => $access_hash[tenant],
        controller_node      => $controller_node_address,
      }

      class { 'openstack::img::cirros':
        os_username               => $access_hash[user],
        os_password               => $access_hash[password],
        os_tenant_name            => $access_hash[tenant],
        img_name                  => "TestVM",
      }

      Class[osnailyfacter::network_setup] -> Class[openstack::controller]
      Class[glance::api]        -> Class[openstack::img::cirros]
    }

    "compute" : {
      include osnailyfacter::test_compute

      class { 'openstack::compute':
        public_interface       => $public_interface,
        private_interface      => $private_interface,
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
        db_host                => $conrtoller_node_address,
        verbose                => $verbose,
      }
      nova_config { 'DEFAULT/start_guests_on_host_boot': value => $start_guests_on_host_boot }
      nova_config { 'DEFAULT/use_cow_images': value => $use_cow_images }
      nova_config { 'DEFAULT/compute_scheduler_driver': value => $compute_scheduler_driver }

      Class[osnailyfacter::network_setup] -> Class[openstack::compute]
    }
  }
}
