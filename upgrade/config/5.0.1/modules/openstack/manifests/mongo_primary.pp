# == Class: openstack::mongo_primary

class openstack::mongo_primary (
  $ceilometer_database          = "ceilometer",
  $ceilometer_user              = "ceilometer",
  $ceilometer_metering_secret   = undef,
  $ceilometer_db_password       = "ceilometer",
  $ceilometer_metering_secret   = "ceilometer",
  $ceilometer_replset_members   = ['mongo2', 'mongo3'],
  $mongodb_bind_address         = ['0.0.0.0'],
  $mongodb_port                 = 27017,
  $use_syslog                   = true,
  $verbose                      = false,
) {

  if size($ceilometer_replset_members) > 0 {
    $replset_setup = true
    $keyfile = '/etc/mongodb.key'
    $replset = 'ceilometer'
  } else {
    $replset_setup = false
    $keyfile = undef
    $replset = undef
  }

  notify {"MongoDB params: $mongodb_bind_address" :} ->

  class {'::mongodb::client':
  } ->

  class {'::mongodb::server':
    port       => $mongodb_port,
    verbose    => $verbose,
    use_syslog => $use_syslog,
    bind_ip    => $mongodb_bind_address,
    auth       => true,
    replset    => $replset,
    keyfile    => $keyfile,
  } ->

  class {'::mongodb::replset':
    replset_setup   => $replset_setup,
    replset_members => $ceilometer_replset_members,
  } ->

  notify {"mongodb configuring databases" :} ->

  mongodb::db { $ceilometer_database:
    user          => $ceilometer_user,
    password      => $ceilometer_db_password,
    roles         => [ 'readWrite', 'dbAdmin', 'dbOwner' ],
    admin_username => 'admin',
    admin_password => $ceilometer_db_password,
    admin_database => 'admin',
  } ->

  mongodb::db { 'admin':
    user         => 'admin',
    password     => $ceilometer_db_password,
    roles        => [
      'userAdmin',
      'readWrite',
      'dbAdmin',
      'dbAdminAnyDatabase',
      'readAnyDatabase',
      'readWriteAnyDatabase',
      'userAdminAnyDatabase',
      'clusterAdmin',
      'clusterManager',
      'clusterMonitor',
      'hostManager',
      'root',
      'restore',
    ],
    admin_username => 'admin',
    admin_password => $ceilometer_db_password,
    admin_database => 'admin',
  } ->

  notify {"mongodb primary finished": }

}
