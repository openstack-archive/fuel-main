node default {
  
  class { "puppetmaster" :
    puppet_master_hostname => "product-centos.mirantis.com"
  } ->

  class { "puppetmaster::nginx-service": }

}
