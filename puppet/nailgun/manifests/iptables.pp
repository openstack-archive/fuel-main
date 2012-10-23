class nailgun::iptables {

  define access_to_nailgun_port($port, $protocol='tcp') {
    $rule = "-p $protocol -m state --state NEW -m $protocol --dport $port -j ACCEPT"
    exec { "access_to_cobbler_${protocol}_port: $port":
      command => "iptables -t filter -I INPUT 1 $rule; \
      /etc/init.d/iptables save",
      unless => "iptables -t filter -S INPUT | grep -q \"^-A INPUT $rule\""
    }
  }

  access_to_nailgun_port { "nailgun_web":    port => '8000' }
  access_to_nailgun_port { "nailgun_repo":    port => '8080' }
  
}
