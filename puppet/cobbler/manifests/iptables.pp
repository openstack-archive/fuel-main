class cobbler::iptables {

  define access_to_cobbler_port($port, $protocol='tcp') {
    $rule = "-p $protocol -m state --state NEW -m $protocol --dport $port -j ACCEPT"
    case $operatingsystem {
      /(?i)(centos|redhat)/: {
        exec { "access_to_cobbler_${protocol}_port: $port":
          command => "iptables -t filter -I INPUT 1 $rule; \
          /etc/init.d/iptables save",
          unless => "iptables -t filter -S INPUT | grep -q \"^-A INPUT $rule\"",
          path => '/usr/bin:/bin:/usr/sbin:/sbin',
        }
      }
      /(?i)(debian|ubuntu)/: {
        exec { "access_to_cobbler_${protocol}_port: $port":
          command => "iptables -t filter -I INPUT 1 $rule; \
          iptables-save -c > /etc/iptables.rules",
          unless => "iptables -t filter -S INPUT | grep -q \"^-A INPUT $rule\"",
          path => '/usr/bin:/bin:/usr/sbin:/sbin',
        }
      }
    }
  }

  case $operatingsystem {
    /(?i)(debian|ubuntu)/:{
      file { "/etc/network/if-post-down.d/iptablessave":
        content => template("cobbler/ubuntu/iptablessave.erb"),
        owner => root,
        group => root,
        mode => 0755,
      }
      file { "/etc/network/if-pre-up.d/iptablesload":
        content => template("cobbler/ubuntu/iptablesload.erb"),
        owner => root,
        group => root,
        mode => 0755,
      }
    }
  }

  # HERE IS IPTABLES RULES TO MAKE COBBLER AVAILABLE FROM OUTSIDE
  # https://github.com/cobbler/cobbler/wiki/Using%20Cobbler%20Import
  # SSH
  access_to_cobbler_port { "ssh":        port => '22' }
  # DNS
  access_to_cobbler_port { "dns_tcp":    port => '53' }
  access_to_cobbler_port { "dns_udp":    port => '53',  protocol => 'udp' }
  # DHCP
  access_to_cobbler_port { "dhcp_67":    port => '67',  protocol => 'udp' }
  access_to_cobbler_port { "dhcp_68":    port => '68',  protocol => 'udp' }
  # SQUID PROXY
  access_to_cobbler_port { "http_3128":  port => '3128',protocol => 'tcp' }
  # PXE
  access_to_cobbler_port { "pxe_4011":   port => '4011',protocol => 'udp' }
  # TFTP
  access_to_cobbler_port { "tftp_tcp":   port => '69' }
  access_to_cobbler_port { "tftp_udp":   port => '69',  protocol => 'udp' }
  # NTP
  access_to_cobbler_port { "ntp_udp":    port => '123', protocol => 'udp' }
  # HTTP/HTTPS
  access_to_cobbler_port { "http":       port => '80' }
  access_to_cobbler_port { "https":      port => '443'}
  # SYSLOG FOR COBBLER
  access_to_cobbler_port { "syslog_tcp": port => '25150'}
  # xmlrpc API
  access_to_cobbler_port { "xmlrpc_api": port => '25151' }


}
