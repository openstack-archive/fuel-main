$openstack_version = {
  'keystone'   => 'latest',
  'glance'     => 'latest',
  'horizon'    => 'latest',
  'nova'       => 'latest',
  'novncproxy' => 'latest',
  'cinder'     => 'latest',
}

$deployment_id = '1'
tag("${::deployment_id}::${::environment}")

node default {
  include osnailyfacter
}
