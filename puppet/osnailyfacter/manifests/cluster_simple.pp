class osnailyfacter::cluster_simple {
  ####### shared variables ##################


  # this section is used to specify global variables that will
  # be used in the deployment of multi and single node openstack
  # environments

  # assumes that eth1 is the public interface
  #$public_interface        = 'eth1' # Provided by Astute
  # assumes that eth0 is the interface that will be used for the vm network
  # this configuration assumes this interface is active but does not have an
  # ip address allocated to it.
  #$internal_interface      = 'eth0' # Provided by Astute
  #$private_interface       = 'eth2' # Provided by Astute

  #$fixed_network_range     = '10.0.214.0/24' # Provided by Astute
  #$floating_network_range  = '10.0.74.128/28' # Provided by Astute

  #$controller_node_address  = '10.0.125.3' # Provided by Astute
  #$controller_node_public   = '10.0.74.3' # Provided by Astute

  $mirror_type='external'

  # credentials
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

  $quantum                = false # true
  $quantum_user_password  = 'quantum_pass'
  $quantum_db_password    = 'quantum_pass'
  $quantum_db_user        = 'quantum'
  $quantum_db_dbname      = 'quantum'
  $tenant_network_type    = 'gre'

  # by default it does not enable atomatically adding floating IPs
  $auto_assign_floating_ip = false
  $manage_volumes         = false # true

  # Add physical volume to cinder, value must be different
  #$nv_physical_volume     = ['/dev/sdz', '/dev/sdy', '/dev/sdx']
  $cinder                 = false # true


  # Moved to the global namespace
  #$openstack_version = {
  #  'keystone'   => latest,
  #  'glance'     => latest,
  #  'horizon'    => latest,
  #  'nova'       => latest,
  #  'novncproxy' => latest,
  #  'cinder' => latest,
  #}

  # switch this to true to have all service log at verbose
  $verbose                 = true

  #stage { 'openstack-custom-repo': before => Stage['main'] }
  #class { 'openstack::mirantis_repos': stage => 'openstack-custom-repo', type => $mirror_type }

  $controller_node_internal = $controller_node_address
  $quantum_host             = $controller_node_address
  $quantum_sql_connection   = "mysql://${quantum_db_user}:${quantum_db_password}@${quantum_host}/${quantum_db_dbname}"
  $sql_connection         = "mysql://nova:${nova_db_password}@${controller_node_internal}/nova"

  case $role {
    "controller" : {
      include osnailyfacter::test_controller

      class { 'openstack::controller':
        admin_address           => $controller_node_internal,
        public_address          => $controller_node_public,
        public_interface        => $public_interface,
        private_interface       => $private_interface,
        internal_address        => $controller_node_internal,
        floating_range          => $floating_network_range,
        fixed_range             => $fixed_network_range,
        # by default it does not enable multi-host mode
        multi_host              => true,
        # by default is assumes flat dhcp networking mode
        network_manager         => 'nova.network.manager.FlatDHCPManager',
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
        quantum_user_password   => $quantum_user_password,
        quantum_db_password     => $quantum_db_password,
        quantum_db_user         => $quantum_db_user,
        quantum_db_dbname       => $quantum_db_dbname,
        tenant_network_type     => $tenant_network_type,
        cinder                  => $cinder,
        manage_volumes          => $manage_volumes,
        nv_physical_volume      => $nv_physical_volume,
      }
      class { 'openstack::auth_file':
        admin_password       => $admin_password,
        keystone_admin_token => $keystone_admin_token,
        controller_node      => $controller_node_internal,
      }
      Class[osnailyfacter::network_setup] -> Class[openstack::controller]
      Class[osnailyfacter::network_setup] -> Class[openstack::auth_file]
    }

    "compute" : {
      include osnailyfacter::test_compute

      class { 'openstack::compute':
        public_interface       => $public_interface,
        private_interface      => $private_interface,
        internal_address       => getvar("::ipaddress_${internal_interface}"),
        libvirt_type           => 'kvm',
        fixed_range            => $fixed_network_range,
        network_manager        => 'nova.network.manager.FlatDHCPManager',
        multi_host             => true,
        sql_connection         => $sql_connection,
        nova_user_password     => $nova_user_password,
        rabbit_nodes           => [$controller_node_internal],
        rabbit_password        => $rabbit_password,
        rabbit_user            => $rabbit_user,
        glance_api_servers     => "${controller_node_internal}:9292",
        vncproxy_host          => $controller_node_public,
        vnc_enabled            => true,
        #ssh_private_key        => 'puppet:///ssh_keys/openstack',
        #ssh_public_key         => 'puppet:///ssh_keys/openstack.pub',
        quantum                => $quantum,
        quantum_host           => $quantum_host,
        quantum_sql_connection => $quantum_sql_connection,
        quantum_user_password  => $quantum_user_password,
        tenant_network_type    => $tenant_network_type,
        service_endpoint       => $controller_node_internal,
        verbose                => $verbose,
      }
      Class[osnailyfacter::network_setup] -> Class[openstack::compute]
    }
  }
}
