class heat::engine (
  $pacemaker             = false,
  $ocf_scripts_dir       = '/usr/lib/ocf/resource.d',
  $ocf_scripts_provider  = 'mirantis',
) {

  include heat::params

  $service_name = $::heat::params::engine_service_name
  $package_name = $::heat::params::engine_package_name
  $pacemaker_service_name = "p_${service_name}"

  package { 'heat-engine' :
    ensure => installed,
    name   => $package_name,
  }

  if !$pacemaker {

    # standard service mode

    service { 'heat-engine_service':
      ensure     => 'running',
      name       => $service_name,
      enable     => true,
      hasstatus  => true,
      hasrestart => true,
    }

  } else {

    # pacemaker resource mode

    if $::osfamily == 'RedHat' {
      $ocf_script_template = 'heat_engine_centos.ocf.erb'
    } else {
      $ocf_script_template = 'heat_engine_ubuntu.ocf.erb'
    }

    file { 'heat-engine-ocf' :
      ensure  => present,
      path    => "${ocf_scripts_dir}/${ocf_scripts_provider}/${service_name}",
      mode    => '0755',
      owner   => 'root',
      group   => 'root',
      content => template("heat/${ocf_script_template}"),
    }

    service { 'heat-engine_service' :
      ensure     => 'running',
      name       => $pacemaker_service_name,
      enable     => true,
      hasstatus  => true,
      hasrestart => true,
      provider   => 'pacemaker',
    }

    service { 'heat-engine_stopped' :
      name   => $service_name,
      ensure => 'stopped',
      enable => false,
    }

    cs_shadow { $pacemaker_service_name :
      cib => $pacemaker_service_name,
    }

    cs_commit { $pacemaker_service_name :
      cib => $pacemaker_service_name,
    }

    cs_resource { $pacemaker_service_name :
      ensure          => present,
      cib             => $pacemaker_service_name,
      primitive_class => 'ocf',
      provided_by     => $ocf_scripts_provider,
      primitive_type  => $service_name,
      metadata        => { 'resource-stickiness' => '1' },
      operations   => {
        'monitor'  => { 'interval' => '20', 'timeout'  => '30' },
        'start'    => { 'timeout' => '60' },
        'stop'     => { 'timeout' => '60' },
      },
    }

    # remove old service from 5.0 release
    $wrong_service_name = $service_name

    cs_resource { $wrong_service_name :
      ensure => 'absent',
      cib    => $pacemaker_service_name,
    }

    Heat_config<||> ->
    File['heat-engine-ocf'] ->
    Cs_shadow[$pacemaker_service_name] ->
    Cs_resource[$service_name] ->
    Cs_resource[$pacemaker_service_name] ->
    Cs_commit[$pacemaker_service_name] ->
    Service['heat-engine_stopped'] ->
    Service['heat-engine_service']

  }

  exec {'heat-encryption-key-replacement':
    command => 'sed -i "s/%ENCRYPTION_KEY%/`hexdump -n 16 -v -e \'/1 "%02x"\' /dev/random`/" /etc/heat/heat.conf',
    path    => [ '/usr/bin', '/bin' ],
    onlyif  => 'grep -c ENCRYPTION_KEY /etc/heat/heat.conf',
  }

  Package['heat-common'] -> Package['heat-engine'] -> File['/etc/heat/heat.conf'] -> Heat_config<||> ~> Service['heat-engine_service']
  File['/etc/heat/heat.conf'] -> Exec['heat-encryption-key-replacement'] -> Service['heat-engine_service']
  File['/etc/heat/heat.conf'] ~> Service['heat-engine_service']
  Class['heat::db'] -> Service['heat-engine_service']
  Heat_config<||> -> Exec['heat_db_sync'] ~> Service['heat-engine_service']
  Package<| title == 'heat-engine'|> ~> Service<| title == 'heat-engine_service'|>
  if !defined(Service['heat-engine_service']) {
    notify{ "Module ${module_name} cannot notify service heat-engine on package update": }
  }
}
