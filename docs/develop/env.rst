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
    sudo pip install fysom jsonschema

#. Install and configure PostgreSQL database::

    sudo apt-get install postgresql postgresql-server-dev-9.1
    sudo -u postgres createuser -DSP nailgun (enter password nailgun)
    sudo -u postgres createdb nailgun

#. Create required folder for log files::

    sudo mkdir /var/log/nailgun
    sudo chown -R `whoami`.`whoami` /var/log/nailgun

#. Run the Nailgun backend unit tests::

    cd nailgun
    ./run_tests.sh --no-jslint --no-ui-tests

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

Installing Cobbler
------------------

Install Cobbler from GitHub (it can't be installed from PyPi, and deb
package in Ubuntu is outdated)::

    cd ~
    git clone git://github.com/cobbler/cobbler.git
    cd cobbler
    git checkout release24
    sudo make install

Building the Fuel ISO
---------------------

#. Follow these steps to prepare an environment for building::

    sudo apt-get install ruby-dev ruby-builder bundler libmysqlclient-dev
    sudo apt-get install yum-utils kpartx extlinux genisoimage isomd5sum

#. ISO build process requires sudo permissions, allow yourself to run
   commands as root user without request for a password::

    echo "`whoami` ALL=(ALL) NOPASSWD: ALL" | sudo tee -a /etc/sudoers

#. Now you can build the Fuel ISO image::

    make iso

Building Documentation
----------------------

#. You will need the following software to build documentation::

    sudo apt-get install rst2pdf python-sphinx python-sphinxcontrib.blockdiag
    pip install sphinxcontrib-plantuml

#. Look at the list of available formats and generate the one you need::

    cd docs
    make help
    make html

You will also need to install Java and PlantUML to automatically
generate UML diagrams from the source. You can also use `PlantUML Server
<http://www.plantuml.com/plantuml/>`_ for a quick preview of your
diagrams.
