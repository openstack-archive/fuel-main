# = Класс: motd
#
# Демонстрационный класс, который создаёт файл /etc/motd.
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
