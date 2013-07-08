class puppetmaster::params 
 {
    case $::osfamily {
    'RedHat': {
         $puppet_master_version  = "2.7.19-1.el6"
         $puppet_master_packages = ["puppet-server", "puppet"] 
         $mongrel_packages = "rubygem-mongrel"
         $thin_packages = "rubygem-thin"
         $daemon_config_file = "/etc/sysconfig/puppetmaster"
         $daemon_config_template = "puppet/sysconfig_puppetmaster.erb"
         $puppet_config_template = "puppet/puppet.conf.centos.erb"
      }
      'Debian': {
         $puppet_master_version  = "2.7.19-1puppetlabs2"
         $puppet_master_packages = ["puppetmaster", "puppetmaster-common", "puppet-common"]
         $mongrel_packages = "mongrel"
         $thin_packages = "thin"
         $daemon_config_file = "/etc/default/puppetmaster"
         $daemon_config_template = "puppet/default_puppetmaster.erb"
         $puppet_config_template = "puppet/puppet.conf.ubuntu.erb"
      }
      default: {
        fail("Unsupported osfamily: ${::osfamily} operatingsystem: ${::operatingsystem}, module ${module_name} only support osfamily RedHat and Debian")
      }
  } 
	  
	 
	case $::osfamily {
	    'RedHat': {
	       $mysql_packages = ['mysql',  'mysql-server', 'mysql-devel', 'rubygems', 'ruby-devel',  'make',  'gcc']      
	    }
	    'Debian': {
	       $mysql_packages = ['mysql-server', 'libmysql-ruby', 'rubygems', 'make',  'gcc']  
	    }
	    default: {
	      fail("Unsupported osfamily: ${::osfamily} operatingsystem: ${::operatingsystem}, module ${module_name} only support osfamily RedHat and Debian")
	    }
	}
  
}
