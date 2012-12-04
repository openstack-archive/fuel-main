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
