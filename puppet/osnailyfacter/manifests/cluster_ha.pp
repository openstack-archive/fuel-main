class osnailyfacter::cluster_ha {

# TODO: move it to astude
$internal_virtual_ip = '192.168.0.253'
$public_virtual_ip = '240.0.1.253'
$master_hostname = 'slave-1'
$controller_public_addresses = {'slave-1' => '10.0.101.3','slave-2' => '10.0.101.4','slave-3' => '10.0.101.5'}
$controller_internal_addresses = {'slave-1' => '192.168.0.2','slave-2' => '192.168.0.3','slave-3' => '192.168.0.4'}
$controller_hostnames = ['slave-1', 'slave-2', 'slave-3']
$swift_zone = 1 # Different for each controller
$swift_proxy_address = $internal_virtual_ip
$internal_address = '192.168.0.2'

##
# These parameters should be edit
##

# This interface will be giving away internet
#$public_interface = 'eth1' # Provided by Astute
# This interface will look to management network
#$internal_interface = 'eth0' # Provided by Astute
# This interface for internal services
#$private_interface = 'eth2' # Provided by Astute

# Public and Internal VIPs for load-balancers
#$internal_virtual_ip = '10.0.126.253' # Provided by Astute
#$public_virtual_ip = '10.0.215.253' # Provided by Astute
#$swift_proxy_address = '10.0.126.253' # Provided by Astute

#$controller_internal_addresses = {'fuel-01' => '10.0.126.3','fuel-02' => '10.0.126.4','fuel-03' => '10.0.126.5'} # Provided by Astute

# Public and Internal IP pools
$create_networks = true
#$fixed_range     = '10.0.198.128/27' # Provided by Astute as fixed_network_range
#$floating_range  = '10.0.74.128/28' # Provided by Astute as floating_network_range

##
# These parameters to change by necessity
##

# Enabled or disabled different services
$multi_host              = true
$quantum                 = false # true
$manage_volumes          = true
$cinder                  = true
$auto_assign_floating_ip = false
$glance_backend          = 'swift'

# Set default hostname
#$master_hostname = 'fuel-01' # Provided by Astute
#$controller_hostnames = ['fuel-01', 'fuel-02', 'fuel-03'] # Provided by Astute
$swift_master = $master_hostname
$swift_proxies = $controller_internal_addresses
$network_manager = 'nova.network.manager.FlatDHCPManager'
#$mirror_type='external'

# Add physical volume to cinder, value must be different
#$nv_physical_volume     = ['/dev/sdz', '/dev/sdy', '/dev/sdx'] 

# Set credential for different services
$swift_shared_secret  = 'changeme'
$swift_user_password     = 'swift_pass'

$mysql_root_password     = 'nova'
$admin_email             = 'openstack@openstack.org'
$admin_password          = 'nova'

$keystone_db_password    = 'nova'
$keystone_admin_token    = 'nova'

$glance_db_password      = 'nova'
$glance_user_password    = 'nova'

$nova_db_password        = 'nova'
$nova_user_password      = 'nova'

$rabbit_password         = 'nova'
$rabbit_user             = 'nova'

$quantum_user_password  = 'quantum_pass'
$quantum_db_password    = 'quantum_pass'
$quantum_db_user        = 'quantum'
$quantum_db_dbname      = 'quantum'
$quantum_sql_connection   = "mysql://${quantum_db_user}:${quantum_db_password}@${quantum_host}/${quantum_db_dbname}"

$controller_node_public   = $internal_virtual_ip
$quantum_host             = $internal_virtual_ip
$swift_local_net_ip       = $ipaddress_eth0

# Moved to the global namespace
#$openstack_version = {
#  'keystone'   => 'latest',
#  'glance'     => 'latest',
#  'horizon'    => 'latest',
#  'nova'       => 'latest',
#  'novncproxy' => 'latest',
#  'cinder' => latest,
#}

$tenant_network_type    = 'gre'
#$internal_address = getvar("::ipaddress_${internal_interface}") # Provided by Astute
$verbose = true
Exec { logoutput => true }

#stage { 'openstack-custom-repo': before => Stage['main'] }
#class { 'openstack::mirantis_repos': stage => 'openstack-custom-repo', type=> $mirror_type }

# deprecated. keep it for backward compatibility
#$controller_public_addresses = {'fuel-01' => '10.0.215.3','fuel-02' => '10.0.215.4','fuel-03' => '10.0.215.5'} # Provided by Astute

class compact_controller {
  class { 'openstack::controller_ha':
    controller_public_addresses   => $controller_public_addresses,
    controller_internal_addresses => $controller_internal_addresses,
    internal_address        => $internal_address,
    public_interface        => $public_interface,
    internal_interface      => $internal_interface,
    private_interface       => $private_interface,
    internal_virtual_ip     => $internal_virtual_ip,
    public_virtual_ip       => $public_virtual_ip,
    master_hostname         => $master_hostname,
    floating_range          => $floating_network_range, #$floating_range,
    fixed_range             => $fixed_network_range, #$fixed_range,
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
    rabbit_nodes            => $controller_hostnames,
    memcached_servers       => $controller_hostnames,
    export_resources        => false,
    glance_backend          => $glance_backend,
    swift_proxies           => $swift_proxies,
    quantum                 => $quantum,
    quantum_user_password   => $quantum_user_password,
    quantum_db_password     => $quantum_db_password,
    quantum_db_user         => $quantum_db_user,
    quantum_db_dbname       => $quantum_db_dbname,
    tenant_network_type     => $tenant_network_type,
    cinder                  => $cinder,
    manage_volumes          => $manage_volumes,
    galera_nodes            => $controller_hostnames,
    nv_physical_volume      => $nv_physical_volume,
  }
  class { 'swift::keystone::auth':
    password         => $swift_user_password,
    public_address   => $public_virtual_ip,
    internal_address => $internal_virtual_ip,
    admin_address    => $internal_virtual_ip,
  }
}

  case $role {
    "controller" : {
      include osnailyfacter::test_controller

      class { 'compact_controller': }
      #$swift_zone = 1 # Provided by Astute

      class { 'openstack::swift::storage-node':
        swift_zone         => $swift_zone,
        swift_local_net_ip => $internal_address,
      }

      class { 'openstack::swift::proxy':
        swift_proxies           => $swift_proxies,
        swift_master            => $swift_master,
        controller_node_address => $internal_virtual_ip,
        swift_local_net_ip      => $internal_address,
      }
      Class[osnailyfacter::network_setup] -> Class[openstack::controller_ha]
      Class[osnailyfacter::network_setup] -> Class[openstack::auth_file]
    }

    "compute" : {
      include osnailyfacter::test_compute

      class { 'openstack::compute':
        public_interface       => $public_interface,
        private_interface      => $private_interface,
        internal_address       => $internal_address,
        libvirt_type           => 'qemu',
        fixed_range            => $fixed_network_range, #$fixed_range,
        network_manager        => $network_manager,
        multi_host             => $multi_host,
        sql_connection         => "mysql://nova:${nova_db_password}@${internal_virtual_ip}/nova",
        rabbit_nodes           => $controller_hostnames,
        rabbit_password        => $rabbit_password,
        rabbit_user            => $rabbit_user,
        glance_api_servers     => "${internal_virtual_ip}:9292",
        vncproxy_host          => $public_virtual_ip,
        verbose                => $verbose,
        vnc_enabled            => true,
        manage_volumes         => false,
        nova_user_password     => $nova_user_password,
        cache_server_ip        => $controller_hostnames,
        service_endpoint       => $internal_virtual_ip,
        quantum                => $quantum,
        quantum_host           => $quantum_host,
        quantum_sql_connection => $quantum_sql_connection,
        quantum_user_password  => $quantum_user_password,
        #tenant_network_type    => $tenant_network_type,
        cinder                 => $cinder,
        #ssh_private_key        => 'puppet:///ssh_keys/openstack',
        #ssh_public_key         => 'puppet:///ssh_keys/openstack.pub',
      }
      Class[osnailyfacter::network_setup] -> Class[openstack::compute]
    }
  }
}
