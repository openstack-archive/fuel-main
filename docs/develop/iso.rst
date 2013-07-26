ISO Build Instructions
======================

Prepare environment
-------------------

All our development is commonly done on Ubuntu 12.10. Follow the steps to prepare an environment (use nodejs package if you run on Ubuntu 12.04)::

    sudo apt-get install ruby python-setuptools yum yum-utils libmysqlclient-dev isomd5sum
    sudo apt-get install python-nose libvirt-bin python-ipaddr python-paramiko python-yaml
    sudo apt-get install python-pip kpartx extlinux npm nodejs-legacy unzip genisoimage
    sudo gem install bundler -v 1.2.1
    sudo gem install builder
    sudo pip install xmlbuilder jinja2
    sudo npm install -g requirejs

Build requires sudo permissions, allow yourself to run commands as root user without request for a password::

    echo "`whoami` ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

Clone repo from github::

    git clone https://github.com/Mirantis/fuelweb.git
    git submodule init
    git submodule update

Now you can build an iso::

    make iso
