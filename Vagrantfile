# -*- mode: ruby -*-
# vi: set ft=ruby :

ENVIRONMENT_SETUP_SCRIPT = <<-EOS
#!/bin/bash
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
    
    # extra network for testing
    vm_config.vm.network :hostonly, '10.1.1.2', :adapter => 2

    vm_config.vm.provision :shell, :inline => ENVIRONMENT_SETUP_SCRIPT
  end
end
