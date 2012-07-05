# -*- mode: ruby -*-
# vi: set ft=ruby :

UBUNTU_BOX_NAME = "ubuntu-12.04-server-amd64-002"
UBUNTU_BOX_URL  = "http://mc0n1-srt.srt.mirantis.net/#{UBUNTU_BOX_NAME}.box"

CENTOS_BOX_NAME = "centos-6.2-server-amd64-002"
CENTOS_BOX_URL  = "http://mc0n1-srt.srt.mirantis.net/#{CENTOS_BOX_NAME}.box"

ENVIRONMENT_SETUP_SCRIPT = <<-EOS
#!/bin/bash

# install nailgun
mkdir -p /opt
cp -r /vagrant/nailgun /opt/

# install eggs & gems
mkdir -p /var/lib/mirror/ubuntu
cp -r /vagrant/binaries/eggs /var/lib/mirror
cp -r /vagrant/binaries/gems /var/lib/mirror

# install bootstrap
mkdir -p /var/lib/mirror/bootstrap
cp -r /vagrant/binaries/bootstrap/linux     /var/lib/mirror/bootstrap/
cp -r /vagrant/binaries/bootstrap/initrd.gz /var/lib/mirror/bootstrap/

mkdir -p /tmp/chef
cat <<-EOF > /tmp/chef/solo.rb
cookbook_path ['/vagrant/cookbooks', '/vagrant/cooks/cookbooks']
EOF

cat <<-EOF > /tmp/chef/solo.json
{
  "cobbler":{
    "updns":"8.8.8.8"
  },
  "nailgun":{
    "root":"/opt/nailgun",
    "user":"nailgun",
    "group":"nailgun"
  },
  "recipes": [ 
    "nailgun::network"
  ]
}
EOF

EOS


Vagrant::Config.run do |config|
  config.vm.define :default do |devbox_config|
    devbox_config.vm.box = UBUNTU_BOX_NAME
    devbox_config.vm.box_url = UBUNTU_BOX_URL

    devbox_config.vm.forward_port 80, 8080
    # devbox_config.vm.forward_port 8000, 8000

    devbox_config.vm.provision :chef_solo do |chef|
      chef.cookbooks_path = "vagrant/cookbooks"

      chef.add_recipe 'nailgun::server'
      chef.add_recipe 'libvirt::server'
      chef.add_recipe 'devops::deps'

      chef.json = {
        :celery => { :create_user => true }
      }
    end
  end

  config.vm.define :ubuntu_testbed do |vm_config|
    vm_config.vm.box = UBUNTU_BOX_NAME
    vm_config.vm.box_url = UBUNTU_BOX_URL

    # extra network for testing
    vm_config.vm.network :hostonly, '10.1.1.2', :adapter => 2

    # vm_config.vm.provision :shell, :inline => ENVIRONMENT_SETUP_SCRIPT
  end

  config.vm.define :centos_testbed do |vm_config|
    vm_config.vm.box = CENTOS_BOX_NAME
    vm_config.vm.box_url = CENTOS_BOX_URL

    # extra network for testing
    vm_config.vm.network :hostonly, '10.1.1.2', :adapter => 2

    # vm_config.vm.provision :shell, :inline => ENVIRONMENT_SETUP_SCRIPT
  end
end

