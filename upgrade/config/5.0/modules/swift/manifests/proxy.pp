#
# TODO - assumes that proxy server is always a memcached server
#
# TODO - the full list of all things that can be configured is here
#  https://github.com/openstack/swift/tree/master/swift/common/middleware
#
# Installs and configures the swift proxy node.
#
# [*Parameters*]
#
# [*proxy_local_net_ip*] The address that the proxy will bind to.
#   Required.
# [*port*] The port to which the proxy server will bind.
#   Optional. Defaults to 8080.
# [*pipeline*] The list of elements of the swift proxy pipeline.
#   Currently supports healthcheck, cache, proxy-server, and
#   one of the following auth_types: tempauth, swauth, keystone.
#   Each of the specified elements also need to be declared externally
#   as a puppet class with the exception of proxy-server.
#   Optional. Defaults to ['healthcheck', 'cache', 'tempauth', 'proxy-server']
# [*workers*] Number of threads to process requests.
#  Optional. Defaults to the number of processors.
# [*allow_account_management*]
#   Rather or not requests through this proxy can create and
#   delete accounts. Optional. Defaults to true.
# [*account_autocreate*] Rather accounts should automatically be created.
#  Has to be set to true for tempauth. Optional. Defaults to true.
# [*package_ensure*] Ensure state of the swift proxy package.
#   Optional. Defaults to present.
#
# == Examples
#
# == Authors
#
#   Dan Bode dan@puppetlabs.com
#
# == Copyright
#
# Copyright 2011 Puppetlabs Inc, unless otherwise noted.
#
class swift::proxy(
  $proxy_local_net_ip,
  $port = '8080',
  $pipeline = ['healthcheck', 'cache', 'tempauth', 'proxy-server'],
  $workers = $::processorcount,
  $allow_account_management = true,
  $account_autocreate = true,
  $package_ensure = 'present',
  $debug = false,
  $verbose = true,
  $syslog_log_level = 'WARNING',
) {

  include 'swift::params'
  include 'concat::setup'

  validate_bool($account_autocreate)
  validate_bool($allow_account_management)
  validate_array($pipeline)

  if(member($pipeline, 'tempauth')) {
    $auth_type = 'tempauth'
  } elsif(member($pipeline, 'swauth')) {
    $auth_type = 'swauth'
  } elsif(member($pipeline, 'keystone')) {
    $auth_type = 'keystone'
  } else {
    warning('no auth type provided in the pipeline')
  }

  if(! member($pipeline, 'proxy-server')) {
    warning("swift storage server ${type} must specify ${type}-server")
  }

  if($auth_type == 'tempauth' and ! $account_autocreate ){
    fail("\$account_autocreate must be set to true when auth type is tempauth")
  }
  if $::osfamily == "Debian"
  {
    package { 'swift-plugin-s3':
    ensure => present,
    before=>Package['swift-proxy']
    }
  }

  package { 'swift-proxy':
    name   => $::swift::params::proxy_package_name,
    ensure => $package_ensure,
  }
  Package['swift-proxy'] -> Swift::Ringsync <||>

  concat { '/etc/swift/proxy-server.conf':
    owner   => 'swift',
    group   => 'swift',
    mode    => '0660',
    require => Package['swift-proxy'],
  }

  $required_classes = split(
    inline_template(
      "<%=
          (@pipeline - ['proxy-server']).collect do |x|
            'swift::proxy::' + x
          end.join(',')
      %>"), ',')

  # you can now add your custom fragments at the user level
  concat::fragment { 'swift_proxy':
    target  => "/etc/swift/proxy-server.conf",
    content => template('swift/proxy-server.conf.erb'),
    order   => '00',
    # require classes for each of the elements of the pipeline
    # this is to ensure the user gets reasonable elements if he
    # does not specify the backends for every specified element of
    # the pipeline
    before  => Class[$required_classes],
  }

  service { 'swift-proxy':
    name      => $::swift::params::proxy_service_name,
    ensure    => running,
    enable    => true,
    provider  => $::swift::params::service_provider,
    require   => [Concat['/etc/swift/proxy-server.conf']],
    subscribe => [Concat['/etc/swift/proxy-server.conf']],
  }
}
