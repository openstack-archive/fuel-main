# = Class: motd
#
# Create file /etc/motd.
#
class motd {
  file { '/etc/motd' :
    ensure  => present,
    owner   => 'root',
    group   => 'root',
    mode    => '0644',
    content => 'Hello!',
  }
}
