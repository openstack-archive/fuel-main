Fuel Development Environment
============================

Basic OS for Fuel development is Ubuntu Linux. Setup instructions below
assume Ubuntu 13.04, most of them should be applicable to other Ubuntu
and Debian versions, too.

Each subsequent section below assumes that you have followed the steps
described in all preceding sections. By the end of this document, you
should be able to run and test all key components of Fuel, build Fuel
master node installation ISO, and generate documentation.

Getting the Source Code
-----------------------

Clone the Mirantis FuelWeb repository from GitHub::

    git clone git@github.com:Mirantis/fuelweb.git
    cd fuelweb
    git submodule init
    git submodule update

All sections below assume you start in your clone of this repository.

Setup for Nailgun Unit Tests
----------------------------

#. Install Python dependencies (fysom has no deb package, and the
   jsonschema deb is outdated, so these modules have to be installed
   from PyPi)::

    sudo apt-get install python-dev python-pip python-psycopg2 python-jinja2
    sudo apt-get install python-paste python-yaml python-sqlalchemy python-kombu
    sudo apt-get install python-crypto python-simplejson python-webpy python-nose
    sudo apt-get install python-mock python-decorator python-netaddr python-flake8
    sudo pip install fysom jsonschema hacking==0.7

#. Install and configure PostgreSQL database::

    sudo apt-get install postgresql postgresql-server-dev-9.1
    sudo -u postgres createuser -SDRP nailgun (enter password nailgun)
    sudo -u postgres createdb nailgun

#. Create required folder for log files::

    sudo mkdir /var/log/nailgun
    sudo chown -R `whoami`.`whoami` /var/log/nailgun

#. Run the Nailgun backend unit tests::

    cd nailgun
    ./run_tests.sh --no-jslint --no-ui-tests

#. Run the Nailgun flake8 test::

    cd nailgun
    ./run_tests.sh --flake8

Setup for Web UI Tests
----------------------

#. Install NodeJS (on Debian, you may need to use 'apt-get install -t
   experimental' to get the latest npm)::

    sudo apt-get install npm nodejs-legacy
    sudo npm install -g jslint requirejs

#. Run full Web UI test suite (this will wipe your Nailgun database in
   PostgreSQL)::

    cd nailgun
    ./run_tests.sh --jslint
    ./run_tests.sh --ui-tests

Running Nailgun in Fake Mode
----------------------------

#. Populate the database from fixtures::

    cd nailgun
    ./manage.py syncdb
    ./manage.py loaddefault # It loads all basic fixtures listed in settings.yaml
    ./manage.py loaddata nailgun/fixtures/sample_environment.json  # Loads fake nodes

#. Start application in "fake" mode, when no real calls to orchestrator
   are performed::

    python manage.py run -p 8000 --fake-tasks | egrep --line-buffered -v '^$|HTTP' >> /var/log/nailgun.log 2>&1 &

#. (optional) You can also use --fake-tasks-amqp option if you want to
   make fake environment use real RabbitMQ instead of fake one::

    python manage.py run -p 8000 --fake-tasks-amqp | egrep --line-buffered -v '^$|HTTP' >> /var/log/nailgun.log 2>&1 &

Astute and Naily
----------------

#. Install Ruby dependencies::

    sudo apt-get install gem2deb ruby-activesupport ruby-rspec ruby-mocha ruby-amqp ruby-json mcollective-client
    cd ~
    gem2deb symboltable
    dpkg -i ruby-symboltable_1.0.2-1_all.deb
    git clone git@github.com:nulayer/raemon.git
    cd raemon
    git checkout v0.3.0
    gem build raemon.gemspec
    gem2deb raemon-0.3.0.gem
    dpkg -i ruby-raemon_0.3.0-1_all.deb

#. Run Astute unit tests::

    cd astute
    find spec/unit/ -name '*_spec.rb'|xargs ruby -I.

#. (optional) Run Astute MCollective integration test (you'll need to
   have MCollective server running for this to work)::

    cd astute
    ruby -I. spec/integration/mcollective_spec.rb

Building the Fuel ISO
---------------------

#. Following software is required to build the Fuel ISO images on Ubuntu
   12.10 or newer (on Ubuntu 12.04, use nodejs package instead of
   nodejs-legacy)::

    sudo apt-get install build-essential make git ruby ruby-dev rubygems
    sudo apt-get install python-setuptools yum yum-utils libmysqlclient-dev isomd5sum
    sudo apt-get install python-nose libvirt-bin python-ipaddr python-paramiko python-yaml
    sudo apt-get install python-pip kpartx extlinux npm nodejs-legacy unzip genisoimage
    sudo gem install bundler -v 1.2.1
    sudo gem install builder
    sudo pip install xmlbuilder jinja2
    sudo npm install -g requirejs

#. (alternative) If you have completed the instructions in the previous
   sections of Fuel development environment setup guide, the list of
   additional packages required to build the ISO becomes shorter::

    sudo apt-get install ruby-dev ruby-builder bundler libmysqlclient-dev
    sudo apt-get install yum-utils kpartx extlinux genisoimage isomd5sum

#. ISO build process requires sudo permissions, allow yourself to run
   commands as root user without request for a password::

    echo "`whoami` ALL=(ALL) NOPASSWD: ALL" | sudo tee -a /etc/sudoers

#. If you haven't already done so, get the source code::

    git clone https://github.com/Mirantis/fuelweb.git
    cd fuelweb
    git submodule init
    git submodule update

#. Now you can build the Fuel ISO image::

    make iso

Running the FuelWeb Integration Test
------------------------------------

#. Install libvirt and Devops library dependencies::

    sudo apt-get install libvirt-bin python-libvirt python-ipaddr python-paramiko
    sudo pip install xmlbuilder django==1.4.3

#. Configure permissions for libvirt and relogin or restart your X for
   the group changes to take effect (consult /etc/libvirt/libvirtd.conf
   for the group name)::

    GROUP=`grep unix_sock_group /etc/libvirt/libvirtd.conf|cut -d'"' -f2`
    sudo useradd `whoami` kvm
    sudo useradd `whoami` $GROUP
    chgrp $GROUP /var/lib/libvirt/images
    chmod g+w /var/lib/libvirt/images

#. Clone the Mirantis Devops virtual environment manipulation library
   from GitHub and install it where FuelWeb Integration Test can find
   it::

    git clone git@github.com:Mirantis/devops.git
    cd devops
    python setup.py build
    sudo python setup.py install

#. Configure and populate the Devops DB::

    SETTINGS=/usr/local/lib/python2.7/dist-packages/devops-2.0-py2.7.egg/devops/settings.py
    sed -i "s/'postgres'/'devops'/" $SETTINGS
    echo "SECRET_KEY = 'secret'" >> $SETTINGS
    sudo -u postgres createdb devops
    sudo -u postgres createuser -SDR devops
    django-admin.py syncdb --settings=devops.settings

#. Run the integration test::

    cd fuelweb
    make test-integration

#. To save time, you can execute individual test cases from the
   integration test suite like this::

    cd fuelweb
    export ENV_NAME=fuelweb
    export PUBLIC_FORWARD=nat
    export ISO_PATH=`pwd`/build/iso/fuelweb-centos-6.4-x86_64.iso
    nosetests -w fuelweb_test -s -l DEBUG --with-xunit fuelweb_test.integration.test_admin_node:TestAdminNode.test_cobbler_alive

#. The test harness creates a snapshot of all nodes called 'empty'
   before starting the tests, and creates a new snapshot if a test
   fails. You can revert to a specific snapshot with this command::

    dos.py revert <snapshot_name>

#. To fully reset your test environment, tell the Devops toolkit to erase it::

    dos.py list
    dos.py erase <env_name>

Running Fuel Puppet Modules Unit Tests
--------------------------------------

#. Install PuppetLabs RSpec Helper::

    cd ~
    gem2deb puppetlabs_spec_helper
    sudo dpkg -i ruby-puppetlabs-spec-helper_0.4.1-1_all.deb
    gem2deb rspec-puppet
    sudo dpkg -i ruby-rspec-puppet_0.1.6-1_all.deb

#. Run unit tests for a Puppet module::

    cd fuel/deployment/puppet/module
    rake spec

Installing Cobbler
------------------

Install Cobbler from GitHub (it can't be installed from PyPi, and deb
package in Ubuntu is outdated)::

    cd ~
    git clone git://github.com/cobbler/cobbler.git
    cd cobbler
    git checkout release24
    sudo make install

Building Documentation
----------------------

#. You will need the following software to build documentation::

    sudo apt-get install librsvg2-bin rst2pdf python-sphinx python-sphinxcontrib.blockdiag
    sudo pip install sphinxcontrib-plantuml

#. Look at the list of available formats and generate the one you need::

    cd docs
    make help
    make html

You will also need to install Java and PlantUML to automatically
generate UML diagrams from the source. You can also use `PlantUML Server
<http://www.plantuml.com/plantuml/>`_ for a quick preview of your
diagrams.
