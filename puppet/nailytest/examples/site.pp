#$public_interface        = 'eth0' # Provided by Astute
$internal_interface      = $management_interface  # provided by Astute  # 'eth0.102'
$private_interface       = $fixed_interface  # provided by Astute  # 'eth0.103'

# It's provided by astute
#$fixed_network_range     = '10.0.1.0/24'
#$floating_network_range  = '10.0.204.128/28'

# It's provided by astute
#$controller_node_address  = '10.0.0.2'
#$controller_node_public   = '10.0.203.72'

$openstack_version = {
  'keystone'   => latest,
  'glance'     => latest,
  'horizon'    => latest,
  'nova'       => latest,
  'novncproxy' => latest,
  'cinder' => latest,
}


node default {
  include nailytest
}
