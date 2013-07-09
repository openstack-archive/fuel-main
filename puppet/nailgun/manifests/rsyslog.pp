class nailgun::rsyslog {

  file { "/etc/rsyslog.d/30-remote-log.conf":
    content => template("nailgun/rsyslog/30-remote-log.conf.erb"),
    owner => "root",
    group => "root",
    mode => 0644,
    notify => Service["rsyslog"],
  }

  file { "/etc/rsyslog.d/50-puppet-log.conf":
    content => template("nailgun/rsyslog/50-puppet-log.conf.erb"),
    owner => "root",
    group => "root",
    mode => 0644,
    notify => Service["rsyslog"],
  }

  file { "/etc/sysconfig/rsyslog":
    content => template("nailgun/rsyslog/rsyslog.erb"),
    owner => "root",
    group => "root",
    mode => 0644,
    notify => Service["rsyslog"],
  }

  service { "rsyslog":
    enable => true,
    ensure => "running",
    require => Package["rsyslog"],
  }

}

