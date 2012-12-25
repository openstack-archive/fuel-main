class osnailyfacter::cluster_ha {

#
# Variables provided by astude
#
#$internal_virtual_ip = '192.168.0.253'
#$public_virtual_ip = '240.0.1.253'
#$master_hostname = 'slave-1'
#$controller_public_addresses = {'slave-1' => '10.0.101.3','slave-2' => '10.0.101.4','slave-3' => '10.0.101.5'}
#$controller_internal_addresses = {'slave-1' => '192.168.0.2','slave-2' => '192.168.0.3','slave-3' => '192.168.0.4'}
#$controller_hostnames = ['slave-1', 'slave-2', 'slave-3']
#$swift_zone = 1 # Different for each controller
#$swift_proxy_address = $internal_virtual_ip
#$internal_address = '192.168.0.2'


#
# site_openstack_swift_compact from fuel examples
#

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

# Public and Internal VIPs. These virtual addresses are required by HA topology and will be managed by keepalived.
#$internal_virtual_ip = '10.0.126.253' # Provided by Astute
#$public_virtual_ip   = '10.0.215.253' # Provided by Astute
#$swift_proxy_address = '10.0.126.253' # Swift is turned off

# Map of controller IP addresses on internal interfaces. Must have an entry for every controller node.
#$controller_internal_addresses = {'fuel-controller-01' => '10.0.126.3','fuel-controller-02' => '10.0.126.4','fuel-controller-03' => '10.0.126.5'} # Provided by Astute

# Specify pools for Floating IP and Fixed IP.
# Floating IP addresses are used for communication of VM instances with the outside world (e.g. Internet).
# Fixed IP addresses are typically used for communication between VM instances.
$create_networks = true
#$fixed_range     = '10.0.198.128/27' # Provided by Astute
#$floating_range  = '10.0.74.128/28' # Provided by Astute

# If $external_ipinfo option is not defined the addresses will be calculated automatically from $floating_range:
# the first address will be defined as an external default router
# second address will be set to an uplink bridge interface (br-ex)
# remaining addresses are utilized for ip floating pool
$external_ipinfo = {}
## $external_ipinfo = {
##   'public_net_router' => '10.0.74.129',
##   'ext_bridge'        => '10.0.74.130',
##   'pool_start'        => '10.0.74.131',
##   'pool_end'          => '10.0.74.142',
## }

# For VLAN networks: valid VLAN VIDs are 1 through 4094.
# For GRE networks: Valid tunnel IDs are any 32 bit unsigned integer.
#$segment_range   = '900:999' # Swift is turned off

# Here you can enable or disable different services, based on the chosen deployment topology.
$multi_host              = true
$quantum                 = false # true
$manage_volumes          = false # true
$cinder                  = false # true
$auto_assign_floating_ip = false
$glance_backend          = 'file' # 'swift'

# Use loopback device for swift
# set 'loopback' or false
#$swift_loopback = 'loopback' # Swift is turned off

# Set master hostname for the HA cluster of controller nodes, as well as hostnames for every controller in the cluster.
#$master_hostname = 'fuel-controller-01' # Provided by Astute
#$controller_hostnames = ['fuel-controller-01', 'fuel-controller-02', 'fuel-controller-03'] # Provided by Astute

# Set up OpenStack network manager
$network_manager = 'nova.network.manager.FlatDHCPManager'

# Here you can add physical volumes to cinder. Please replace values with the actual names of devices.
#$nv_physical_volume     = ['/dev/sdz', '/dev/sdy', '/dev/sdx'] # Cinder is turned off

# Specify credentials for different services
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

#$swift_user_password     = 'swift_pass' # Swift is turned off
#$swift_shared_secret     = 'changeme' # Swift is turned off

#$quantum_user_password   = 'quantum_pass' # Quantum is turned off
#$quantum_db_password     = 'quantum_pass' # Quantum is turned off
#$quantum_db_user         = 'quantum' # Quantum is turned off
#$quantum_db_dbname       = 'quantum' # Quantum is turned off
#$tenant_network_type     = 'gre' # Quantum is turned off
#$quantum_host            = $internal_virtual_ip # Quantum is turned off


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

#$internal_address = getvar("::ipaddress_${internal_interface}") # Provided by Astute
#$quantum_sql_connection  = "mysql://${quantum_db_user}:${quantum_db_password}@${quantum_host}/${quantum_db_dbname}" # Quantum is turned off

#$swift_local_net_ip      = $internal_address # Swift is turned off
$controller_node_public  = $internal_virtual_ip
#$swift_master            = $master_hostname # Swift is turned off
#$swift_proxies           = $controller_internal_addresses # Swift is turned off

$verbose = true
Exec { logoutput => true }

# We do not need custom repo
#stage { 'openstack-custom-repo': before => Stage['main'] }
#class { 'openstack::mirantis_repos': stage => 'openstack-custom-repo', type=> $mirror_type }

#if $::operatingsystem == 'Ubuntu' {
#  class { 'openstack::apparmor::disable': stage => 'openstack-custom-repo' }
#}

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
    rabbit_nodes            => $controller_hostnames,
    memcached_servers       => $controller_hostnames,
    export_resources        => false,
    glance_backend          => $glance_backend,
    #swift_proxies           => $swift_proxies,
    #quantum                 => $quantum,
    #quantum_user_password   => $quantum_user_password,
    #quantum_db_password     => $quantum_db_password,
    #quantum_db_user         => $quantum_db_user,
    #quantum_db_dbname       => $quantum_db_dbname,
    #tenant_network_type     => $tenant_network_type,
    #segment_range           => $segment_range,
    cinder                  => $cinder,
    manage_volumes          => $manage_volumes,
    galera_nodes            => $controller_hostnames,
    nv_physical_volume      => $nv_physical_volume,
  }
  #class { 'swift::keystone::auth':
  #  password         => $swift_user_password,
  #  public_address   => $public_virtual_ip,
  #  internal_address => $internal_virtual_ip,
  #  admin_address    => $internal_virtual_ip,
  #}
}

# Definition of OpenStack Quantum node.
#node /fuel-quantum/ {
#    class { 'openstack::quantum_router':
#      db_host               => $internal_virtual_ip,
#      service_endpoint      => $internal_virtual_ip,
#      auth_host             => $internal_virtual_ip,
#      internal_address      => $internal_address,
#      public_interface      => $public_interface,
#      private_interface     => $private_interface,
#      floating_range        => $floating_range,
#      fixed_range           => $fixed_range,
#      create_networks       => $create_networks,
#      verbose               => $verbose,
#      rabbit_password       => $rabbit_password,
#      rabbit_user           => $rabbit_user,
#      rabbit_nodes          => $controller_hostnames,
#      quantum               => $quantum,
#      quantum_user_password => $quantum_user_password,
#      quantum_db_password   => $quantum_db_password,
#      quantum_db_user       => $quantum_db_user,
#      quantum_db_dbname     => $quantum_db_dbname,
#      tenant_network_type   => $tenant_network_type,
#      segment_range         => $segment_range,
#      external_ipinfo       => $external_ipinfo,
#      api_bind_address      => $internal_address
#    }
#
#    class { 'openstack::auth_file':
#      admin_password       => $admin_password,
#      keystone_admin_token => $keystone_admin_token,
#      controller_node      => $internal_virtual_ip,
#      before               => Class['openstack::quantum_router'],
#    }
#}

# This configuration option is deprecated and will be removed in future releases. It's currently kept for backward compatibility.
#$controller_public_addresses = {'fuel-controller-01' => '10.0.215.3','fuel-controller-02' => '10.0.215.4','fuel-controller-03' => '10.0.215.5'} # Provided by Astute


  case $role {
    "controller" : {
      include osnailyfacter::test_controller

      # Definition of the OpenStack controller.
      class { compact_controller: }
      #$swift_zone = 1 # Provided by Astute

      #class { 'openstack::swift::storage-node':
      #  storage_type       => $swift_loopback,
      #  swift_zone         => $swift_zone,
      #  swift_local_net_ip => $internal_address,
      #}

      #class { 'openstack::swift::proxy':
      #  swift_proxies           => $swift_proxies,
      #  swift_master            => $swift_master,
      #  controller_node_address => $internal_virtual_ip,
      #  swift_local_net_ip      => $internal_address,
      #}

      Class[osnailyfacter::network_setup] -> Class[openstack::controller_ha]
      Class[osnailyfacter::network_setup] -> Class[openstack::auth_file]
    }

    "compute" : {
      include osnailyfacter::test_compute

      # Definition of OpenStack compute nodes.
      class { 'openstack::compute':
        public_interface       => $public_interface,
        private_interface      => $private_interface,
        internal_address       => $internal_address,
        libvirt_type           => 'qemu',
        fixed_range            => $fixed_range,
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
        #quantum_host           => $quantum_host,
        #quantum_sql_connection => $quantum_sql_connection,
        #quantum_user_password  => $quantum_user_password,
        #tenant_network_type    => $tenant_network_type,
        #segment_range          => $segment_range,
        cinder                 => $cinder,
        #ssh_private_key        => 'puppet:///ssh_keys/openstack',
        #ssh_public_key         => 'puppet:///ssh_keys/openstack.pub',
      }

      Class[osnailyfacter::network_setup] -> Class[openstack::compute]
    }
  }
}
