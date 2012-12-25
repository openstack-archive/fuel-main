class osnailyfacter::cluster_simple {

#
# Parameter values in this file should be changed, taking into consideration your
# networking setup and desired OpenStack settings.
# 
# Please consult with the latest Fuel User Guide before making edits.
#

# This is a name of public interface. Public network provides address space for Floating IPs, as well as public IP accessibility to the API endpoints.
#$public_interface    = 'eth1' # Provided by Astute

# This is a name of internal interface. It will be hooked to the management network, where data exchange between components of the OpenStack cluster will happen.
#$internal_interface  = 'eth0' # Provided by Astute

# This is a name of private interface. All traffic within OpenStack tenants' networks will go through this interface.
#$private_interface   = 'eth2' # Provided by Astute

# Specify pools for Floating IP and Fixed IP.
# Floating IP addresses are used for communication of VM instances with the outside world (e.g. Internet).
# Fixed IP addresses are typically used for communication between VM instances.
#$floating_range  = '10.0.74.128/28' # Provided by Astute
#$fixed_range     = '10.0.214.0/24' # Provided by Astute

# Here you can enable or disable different services, based on the chosen deployment topology.
$cinder                  = false # true
$multi_host              = true
$manage_volumes          = false # true
$quantum                 = false
$auto_assign_floating_ip = false

# Addresses of controller node
#$controller_node_address = '10.0.125.3' # Provided by Astute
#$controller_node_public  = '10.0.74.3' # Provided by Astute

# Set up OpenStack network manager
$network_manager      = 'nova.network.manager.FlatDHCPManager'

# Here you can add physical volumes to cinder. Please replace values with the actual names of devices.
#$nv_physical_volume   = ['/dev/sdz', '/dev/sdy', '/dev/sdx']

# Specify credentials for different services
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

#$quantum_user_password   = 'quantum_pass' # Quantum is turned off
#$quantum_db_password     = 'quantum_pass' # Quantum is turned off
#$quantum_db_user         = 'quantum' # Quantum is turned off
#$quantum_db_dbname       = 'quantum' # Quantum is turned off
#$tenant_network_type     = 'gre' # Quantum is turned off

$controller_node_internal = $controller_node_address
#$quantum_host             = $controller_node_address
$sql_connection           = "mysql://nova:${nova_db_password}@${controller_node_internal}/nova"
#$quantum_sql_connection   = "mysql://${quantum_db_user}:${quantum_db_password}@${quantum_host}/${quantum_db_dbname}" # Quantum is turned off

# Moved to the global scope
# OpenStack packages to be installed
#$openstack_version = {
#  'keystone'   => 'latest',
#  'glance'     => 'latest',
#  'horizon'    => 'latest',
#  'nova'       => 'latest',
#  'novncproxy' => 'latest',
#  'cinder'     => 'latest',
#}

$mirror_type = 'external'

$verbose = true
Exec { logoutput => true }

#stage { 'openstack-custom-repo': before => Stage['main'] }
#class { 'openstack::mirantis_repos': stage => 'openstack-custom-repo', type => $mirror_type }

#if $::operatingsystem == 'Ubuntu' {
#  class { 'openstack::apparmor::disable': stage => 'openstack-custom-repo' }
#}


  case $role {
    "controller" : {
      include osnailyfacter::test_controller

      # Definition of OpenStack controller node.
      class { 'openstack::controller':
        admin_address           => $controller_node_internal,
        public_address          => $controller_node_public,
        public_interface        => $public_interface,
        private_interface       => $private_interface,
        internal_address        => $controller_node_internal,
        floating_range          => $floating_range,
        fixed_range             => $fixed_range,
        multi_host              => $multi_host,
        network_manager         => $network_manager,
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
        #quantum_user_password   => $quantum_user_password,
        #quantum_db_password     => $quantum_db_password,
        #quantum_db_user         => $quantum_db_user,
        #quantum_db_dbname       => $quantum_db_dbname,
        #tenant_network_type     => $tenant_network_type,
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

      # Definition of OpenStack compute nodes.

      class { 'openstack::compute':
        public_interface       => $public_interface,
        private_interface      => $private_interface,
        internal_address       => getvar("::ipaddress_${internal_interface}"),
        libvirt_type           => 'kvm',
        fixed_range            => $fixed_range,
        network_manager        => $network_manager,
        multi_host             => $multi_host,
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
        #quantum_host           => $quantum_host,
        #quantum_sql_connection => $quantum_sql_connection,
        #quantum_user_password  => $quantum_user_password,
        #tenant_network_type    => $tenant_network_type,
        service_endpoint       => $controller_node_internal,
        verbose                => $verbose,
      }

      Class[osnailyfacter::network_setup] -> Class[openstack::compute]
    }
  }
}
