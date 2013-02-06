# -*- mode: ruby -*-
# vi: set ft=ruby :


ENVIRONMENT_SETUP_SCRIPT = <<-EOS
# To use this script, you must fetch fuel submodule:
#   git submodule update
#!/bin/bash
grep -q devnailgun /etc/hosts || echo "10.0.2.15 devnailgun.mirantis.com devnailgun" >> /etc/hosts
sed 's/HOSTNAME=.*/HOSTNAME=devnailgun.mirantis.com/' -i /etc/sysconfig/network

echo "Installing puppet..."
rpm -Uhv http://fedora-mirror02.rbc.ru/pub/epel/6/i386/epel-release-6-8.noarch.rpm
rpm -ivh http://yum.puppetlabs.com/el/6/products/i386/puppetlabs-release-6-6.noarch.rpm
for pkg in `grep puppet /vagrant/requirements-rpm.txt`; do yum -y install $pkg; done

echo "Configuring puppet..."
grep -q devnailgun /etc/puppet/puppet.conf || echo "    server = devnailgun.mirantis.com" >> /etc/puppet/puppet.conf
grep -q autosign /etc/puppet/puppet.conf || echo "\n[master]\n    autosign = true" >> /etc/puppet/puppet.conf
chkconfig puppetmaster on; service puppetmaster restart

echo "Use fuel puppet modules to install mcollective&rabbitmq"
rm -f /etc/puppet/modules.old || :
mv /etc/puppet/modules /etc/puppet/modules.old || :
ln -sfT /fuel/deployment/puppet /etc/puppet/modules
mv /etc/puppet/manifests/site.pp /etc/puppet/manifests/site.pp.old || :
cat > /etc/puppet/manifests/site.pp << EOF
node default {

  Exec {path => '/usr/bin:/bin:/usr/sbin:/sbin'}

  class { mcollective::rabbitmq:
    stompuser => "mcollective",
    stomppassword => "mcollective",
  }

  class { mcollective::client:
    pskey => "unset",
    stompuser => "mcollective",
    stomppassword => "mcollective",
    stomphost => "127.0.0.1",
    stompport => "61613"
  }

}
EOF
puppet agent --test

echo "Restoring site.pp and modules to previously set.."
mv /etc/puppet/modules.old /etc/puppet/modules || :
mv /etc/puppet/manifests/site.pp.old /etc/puppet/manifests/site.pp || :

echo "Installing mcollective..."
for pkg in `grep mcollective /vagrant/requirements-rpm.txt`; do yum -y install $pkg; done
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

    config.vm.share_folder "v-data", "/fuel", "./fuel"
    
    # extra network for testing
    vm_config.vm.network :hostonly, '10.1.1.2', :adapter => 2

    vm_config.vm.provision :shell, :inline => ENVIRONMENT_SETUP_SCRIPT
  end
end
