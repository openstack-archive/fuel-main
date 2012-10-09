# -*- mode: ruby -*-
# vi: set ft=ruby :

ENVIRONMENT_SETUP_SCRIPT = <<-EOS
#!/bin/bash
echo "10.0.2.15 devnailgun.mirantis.com devnailgun" >> /etc/hosts
sed 's/HOSTNAME=.*/HOSTNAME=devnailgun.mirantis.com/' -i /etc/sysconfig/network
rpm -Uhv http://fedora-mirror02.rbc.ru/pub/epel/6/i386/epel-release-6-7.noarch.rpm
rpm -ivh http://yum.puppetlabs.com/el/6/products/i386/puppetlabs-release-6-6.noarch.rpm
yum -y install puppet-server puppet-2.7.19
echo "    server = devnailgun.mirantis.com" >> /etc/puppet/puppet.conf
echo "    certname = custom_id" >> /etc/puppet/puppet.conf
chkconfig puppetmaster on; service puppetmaster start
puppet agent --test
puppet cert sign custom_id

echo "Use fuel puppet modules to install mcollective&rabbitmq"
ln -sfT /fuel/deployment/puppet /etc/puppet/modules
cat > /etc/puppet/manifests/site.pp << EOF
node default {

  Exec {path => '/usr/bin:/bin:/usr/sbin:/sbin'}

  class { mcollective::rabbitmq:
    stompuser => "mcollective",
    stomppassword => "guest",
  }

  class { mcollective::client:
    pskey => "noset",
    stompuser => "mcollective",
    stomppassword => "guest",
    stomphost => "127.0.0.1",
    stompport => "61613"
  }

}
EOF
puppet agent --test
yum -y install mcollective
chkconfig mcollective on
service mcollective start

# Debug tools
yum -y install strace bind-utils

yum -y install httpd
EOS

Vagrant::Config.run do |config|
  config.vm.define :centos63 do |vm_config|
    vm_config.vm.box = "centos63"
    vm_config.vm.box_url = "http://srv08-srt.srt.mirantis.net/CentOS-6.3-x86_64-minimal.box"
    vm_config.vm.customize ["modifyvm", :id, "--memory", 1024]

    # Boot with a GUI so you can see the screen. (Default is headless)
    #config.vm.boot_mode = :gui

    config.vm.share_folder "v-data", "/opt", "."
    config.vm.share_folder "v-data", "/fuel", "../fuel"
    
    # extra network for testing
    vm_config.vm.network :hostonly, '10.1.1.2', :adapter => 2

    vm_config.vm.provision :shell, :inline => ENVIRONMENT_SETUP_SCRIPT
  end
end
