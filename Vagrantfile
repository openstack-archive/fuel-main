# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant::Config.run do |config|
  config.vm.box = "ubuntu-12.04-server-amd64-002"
  config.vm.box_url = "http://mc0n1-srt.srt.mirantis.net/ubuntu-12.04-server-amd64-002.box"

  config.vm.forward_port 80, 8080
  # config.vm.forward_port 8000, 8000

  config.vm.provision :chef_solo do |chef|
    chef.cookbooks_path = "vagrant/cookbooks"

    chef.add_recipe 'nailgun::server'
    chef.add_recipe 'libvirt::server'
    chef.add_recipe 'devops::deps'

    chef.json = {
      :celery => { :create_user => true }
    }
  end
end
