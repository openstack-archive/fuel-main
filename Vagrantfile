# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant::Config.run do |config|
  config.vm.box = "ubuntu-12.04-server-amd64"
  # config.vm.box_url = "http://domain.com/path/to/above.box"

  config.vm.forward_port 80, 8080
  # config.vm.forward_port 8000, 8000

  config.vm.provision :chef_solo do |chef|
    chef.cookbooks_path = "vagrant/cookbooks"

    chef.add_recipe 'nailgun::server'

    chef.json = {
      :celery => { :create_user => true }
    }
  end
end
