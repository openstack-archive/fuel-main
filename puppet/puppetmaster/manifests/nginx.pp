class puppetmaster::nginx(
  $puppet_master_hostname,
  $crt = "auto",
  $key = "auto",
  $puppet_ca = "/var/lib/puppet/ssl/certs/ca.pem",
  $puppet_crl = "/var/lib/puppet/ssl/crl.pem",
  ) {

  if $crt == "auto" {
    $puppet_master_crt = "/var/lib/puppet/ssl/certs/${puppet_master_hostname}.pem"
  }
  else{
    $puppet_master_crt = $crt
  }

  if $key == "auto" {
    $puppet_master_key = "/var/lib/puppet/ssl/private_keys/${puppet_master_hostname}.pem"
  }
  else{
    $puppet_master_key = $key
  }
  
  file { "/etc/nginx/conf.d/puppet.conf":
    content => template("puppetmaster/nginx_puppet.erb"),
    owner => 'root',
    group => 'root',
    mode => 0644,
    require => Package["nginx"],
    notify => Service["nginx"],
  }

}
