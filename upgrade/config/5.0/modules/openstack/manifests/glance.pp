#
# == Class: openstack::glance
#
# Installs and configures Glance
# Assumes the following:
#   - Keystone for authentication
#   - keystone tenant: services
#   - keystone username: glance
#   - storage backend: file
#
# === Parameters
#
# [db_host] Host where DB resides. Required.
# [glance_user_password] Password for glance auth user. Required.
# [glance_db_password] Password for glance DB. Required.
# [keystone_host] Host whre keystone is running. Optional. Defaults to '127.0.0.1'
# [auth_uri] URI used for auth. Optional. Defaults to "http://${keystone_host}:5000/"
# [db_type] Type of sql databse to use. Optional. Defaults to 'mysql'
# [glance_db_user] Name of glance DB user. Optional. Defaults to 'glance'
# [glance_db_dbname] Name of glance DB. Optional. Defaults to 'glance'
# [verbose] Rather to print more verbose (INFO+) output. If non verbose and non debug, would give
#   syslog_log_level (default is WARNING) output. Optional. Defaults to false.
# [debug] Rather to print even more verbose (DEBUG+) output. If true, would ignore verbose option.
#   Optional. Defaults to false.
# [enabled] Used to indicate if the service should be active (true) or passive (false).
#   Optional. Defaults to true
# [use_syslog] Rather or not service should log to syslog. Optional. Default to false.
# [syslog_log_facility] Facility for syslog, if used. Optional. Note: duplicating conf option
#       wouldn't have been used, but more powerfull rsyslog features managed via conf template instead
# [syslog_log_level] logging level for non verbose and non debug mode. Optional.
# [glance_image_cache_max_size] the maximum size of glance image cache. Optional. Default is 10G.
#
# === Example
#
# class { 'openstack::glance':
#   glance_user_password => 'changeme',
#   db_password          => 'changeme',
#   db_host              => '127.0.0.1',
# }

class openstack::glance (
  $db_host                      = 'localhost',
  $glance_user_password         = false,
  $glance_db_password           = false,
  $bind_host                    = '127.0.0.1',
  $keystone_host                = '127.0.0.1',
  $registry_host                = '127.0.0.1',
  $auth_uri                     = "http://127.0.0.1:5000/",
  $db_type                      = 'mysql',
  $glance_db_user               = 'glance',
  $glance_db_dbname             = 'glance',
  $glance_backend               = 'file',
  $verbose                      = false,
  $debug                        = false,
  $enabled                      = true,
  $use_syslog                   = false,
  # Facility is common for all glance services
  $syslog_log_facility          = 'LOG_LOCAL2',
  $syslog_log_level             = 'WARNING',
  $glance_image_cache_max_size  = '10737418240',
  $idle_timeout                 = '3600',
  $max_pool_size                = '10',
  $max_overflow                 = '30',
  $max_retries                  = '-1',
  $rabbit_password              = false,
  $rabbit_userid                = 'guest',
  $rabbit_host                  = 'localhost',
  $rabbit_port                  = '5672',
  $rabbit_hosts                 = false,
  $rabbit_virtual_host          = '/',
  $rabbit_use_ssl               = false,
  $rabbit_notification_exchange = 'glance',
  $rabbit_notification_topic    = 'notifications',
  $amqp_durable_queues          = false,
) {

  validate_string($glance_user_password)
  validate_string($glance_db_password)
  validate_string($rabbit_password)

  # Configure the db string
  case $db_type {
    'mysql': {
      $sql_connection = "mysql://${glance_db_user}:${glance_db_password}@${db_host}/${glance_db_dbname}?read_timeout=60"
    }
  }

  # Install and configure glance-api
  class { 'glance::api':
    verbose              => $verbose,
    debug                => $debug,
    bind_host            => $bind_host,
    auth_type            => 'keystone',
    auth_port            => '35357',
    auth_host            => $keystone_host,
    keystone_tenant      => 'services',
    keystone_user        => 'glance',
    keystone_password    => $glance_user_password,
    sql_connection       => $sql_connection,
    enabled              => $enabled,
    registry_host        => $registry_host,
    use_syslog           => $use_syslog,
    syslog_log_facility  => $syslog_log_facility,
    syslog_log_level     => $syslog_log_level,
    image_cache_max_size => $glance_image_cache_max_size,
    max_retries          => $max_retries,
    max_pool_size        => $max_pool_size,
    max_overflow         => $max_overflow,
    idle_timeout         => $idle_timeout,
  }

  # Install and configure glance-registry
  class { 'glance::registry':
    verbose             => $verbose,
    debug               => $debug,
    bind_host           => $bind_host,
    auth_host           => $keystone_host,
    auth_port           => '35357',
    auth_type           => 'keystone',
    keystone_tenant     => 'services',
    keystone_user       => 'glance',
    keystone_password   => $glance_user_password,
    sql_connection      => $sql_connection,
    enabled             => $enabled,
    use_syslog          => $use_syslog,
    syslog_log_facility => $syslog_log_facility,
    syslog_log_level    => $syslog_log_level,
    max_retries         => $max_retries,
    max_pool_size       => $max_pool_size,
    max_overflow        => $max_overflow,
    idle_timeout        => $idle_timeout,
  }

  # puppet-glance assumes rabbit_hosts is an array of [node:port, node:port]
  # but we pass it as a amqp_hosts string of 'node:port, node:port' in Fuel
  if !is_array($rabbit_hosts) {
    $rabbit_hosts_real = split($rabbit_hosts, ',')
  } else {
    $rabbit_hosts_real = $rabbit_hosts
  }

  # Configure rabbitmq notifications
  # TODO(bogdando) sync qpid support from upstream
  class { 'glance::notify::rabbitmq':
    rabbit_password              => $rabbit_password,
    rabbit_userid                => $rabbit_userid,
    rabbit_hosts                 => $rabbit_hosts_real,
    rabbit_host                  => $rabbit_host,
    rabbit_port                  => $rabbit_port,
    rabbit_virtual_host          => $rabbit_virtual_host,
    rabbit_use_ssl               => $rabbit_use_ssl,
    rabbit_notification_exchange => $rabbit_notification_exchange,
    rabbit_notification_topic    => $rabbit_notification_topic,
    amqp_durable_queues          => $amqp_durable_queues,
  }

  # Configure file storage backend


 if $glance_backend == "swift" {
    if !defined(Package['swift']) {
      include ::swift::params
      package { "swift":
        name   => $::swift::params::package_name,
        ensure =>present
      }
    }
    Package["swift"] ~> Service['glance-api']
    Package['swift'] -> Swift::Ringsync <||>
    Package<| title == 'swift'|> ~> Service<| title == 'glance-api'|>
    if !defined(Service['glance-api']) {
      notify{ "Module ${module_name} cannot notify service glance-api on package swift update": }
    }

    class { "glance::backend::$glance_backend":
      swift_store_user => "services:glance",
      swift_store_key=> $glance_user_password,
      swift_store_create_container_on_put => "True",
      swift_store_auth_address => "http://${keystone_host}:5000/v2.0/"
    }
  } else {
    class { "glance::backend::$glance_backend": }
  }
}
