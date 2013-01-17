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
$auto_assign_floating_ip = false

$network_manager      = "nova.network.manager.${network_manager}"

$admin_email             = 'root@localhost'
$admin_password          = 'keystone_admin'
$keystone_db_password    = 'keystone_db_pass'
$keystone_admin_token    = 'keystone_admin_token'
$nova_db_password        = 'nova_pass'
$nova_user_password      = 'nova_pass'
$glance_db_password      = 'glance_pass'
$glance_user_password    = 'glance_pass'
$rabbit_password         = 'openstack_rabbit_password'
$rabbit_user             = 'openstack_rabbit_user'

$sql_connection           = "mysql://nova:${nova_db_password}@${controller_node_address}/nova"
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
        mysql_root_password     => $mysql_root_password,
        admin_email             => $admin_email,
        admin_password          => $admin_password,
        keystone_db_password    => $keystone_db_password,
        keystone_admin_token    => $keystone_admin_token,
        glance_db_password      => $glance_db_password,
        glance_user_password    => $glance_user_password,
        nova_db_password        => $nova_db_password,
        nova_user_password      => $nova_user_password,
        rabbit_password         => $rabbit_password,
        rabbit_user             => $rabbit_user,
        export_resources        => false,
        quantum                 => $quantum,
        cinder                  => $cinder,
        manage_volumes          => $manage_volumes,
        nv_physical_volume      => $nv_physical_volume,
      }

      class { 'openstack::auth_file':
        admin_password       => $admin_password,
        keystone_admin_token => $keystone_admin_token,
        controller_node      => $controller_node_address,
      }

      class { 'openstack::img::cirros':
        os_password               => $admin_password,
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
        libvirt_type           => 'kvm',
        fixed_range            => $fixed_network_range,
        network_manager        => $network_manager,
        network_config         => $network_config,
        multi_host             => $multi_host,
        sql_connection         => $sql_connection,
        nova_user_password     => $nova_user_password,
        rabbit_nodes           => [$controller_node_address],
        rabbit_password        => $rabbit_password,
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

      Class[osnailyfacter::network_setup] -> Class[openstack::compute]
    }
  }
}
