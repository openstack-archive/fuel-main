product-and-community
=====================

Deploying virtual environment
-----------------------------

**Using vagrant:**

**Note:** uncomment *config.vm.forward_port 8000, 8000* in Vagrantfile for working with django webui.

For VM deployment run:
`vagrant up`

The working directory is /vagrant.

**W/O vagrant:**

**Installing chef** ([source](http://wiki.opscode.com/display/chef/Installing+Chef+Server+on+Debian+or+Ubuntu+using+Packages "Opscode Wiki")): 

``~$ echo "deb http://apt.opscode.com/ `lsb_release -cs`-0.10 main" | sudo tee /etc/apt/sources.list.d/opscode.list ``
``~$ sudo mkdir -p /etc/apt/trusted.gpg.d
gpg --keyserver keys.gnupg.net --recv-keys 83EF826A
gpg --export packages@opscode.com | sudo tee /etc/apt/trusted.gpg.d/opscode-keyring.gpg > /dev/null ``
`` sudo apt-get update && sudo apt-get install opscode-keyring ``
`` sudo apt-get install chef chef-solo ``

**Installing dependencies**

`` cd scripts/ci && chef-solo -l debug -c solo.rb -j solo.json ``

Testing
-------

**Nailgun:**

Testing script is *nailgun/run_tests.sh*
Test cases:
- nailgun/nailgun/tests/test_handlers.py
- nailgun/nailgun/tests/test_models.py
