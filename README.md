NAILGUN
=======

How to run Nailgun app from fixtures
------------------------------------
Install application dependencies (eggs):

        cd scripts/ci/
        sudo easy_install pip
        sudo chef-solo -c solo.rb -j solo.json
        cd -

Remove old DB:

        cd nailgun
        rm -f nailgun.sqlite

Sync DB:

        ./manage.py syncdb --noinput

Load data from fixtures:

        ./manage.py loaddata sample_environment

Run application:

        ./manage.py runserver

Access Web UI at http://localhost:8000/


Deploying virtual environment
-----------------------------

**Using vagrant:**

**Note:** uncomment *config.vm.forward_port 8000, 8000* in Vagrantfile for working with django webui.

For VM deployment run:
`vagrant up ubuntu_testbed`

The working directory is /vagrant.

**W/O vagrant:**

**Installing chef** ([source](http://wiki.opscode.com/display/chef/Installing+Chef+Server+on+Debian+or+Ubuntu+using+Packages "Opscode Wiki")): 

``~$ echo "deb http://apt.opscode.com/ `lsb_release -cs`-0.10 main" | sudo tee /etc/apt/sources.list.d/opscode.list ``

``~$ sudo mkdir -p /etc/apt/trusted.gpg.d``

``~$ gpg --keyserver keys.gnupg.net --recv-keys 83EF826A``

``~$ gpg --export packages@opscode.com | sudo tee /etc/apt/trusted.gpg.d/opscode-keyring.gpg > /dev/null ``

``~$ sudo apt-get update && sudo apt-get install opscode-keyring ``

``~$ sudo apt-get install chef``

**Installing dependencies**

``~$ cd scripts/ci && chef-solo -l debug -c solo.rb -j solo.json ``

Testing
-------

**Nailgun:**

Unit tests: *make test-unit* or *nailgun/run_tests.sh*
Integration tests: *make test-integration*

Layout
------

    Makefile - the global product makefile
    Vagrantfile - for the vagrant dev vms
    bin/
        create_release - upload a release json file to nailgun (see e.g. scripts/ci/sample-release.json)
        deploy - invoked on a node to deploy; downloads and executes recipes
        install_cookbook - uploads cookbooks to nailgun admin API
    binaries/ - submodule for binaries such as packages and ISO-files
    bootstrap/ - creating a bootstrap image (aka crowbar sledgehammer) for nodes (initrd, configuration files, packages etc) It needed to be refactored to use clear make without calling additional shell scripts.
    cookbooks/ - chef cookbooks to install Nailgun application
        agent/ - node agent. Sends ohai data to admin node.
        nailgun/ - nailgun server (not slave node!)
        others obvious
    cooks/ - submodule with Cookbooks to be loaded in Nailgun app. OpenStack cookbooks will be here.
    devops/ - Mirantis CI framework, used by integration tests (./test/integration/). Installed on the master, not slave.
    gnupg/
    iso/ - creating a main iso to install admin node
    nailgun/ - server
        manage.py, run_tests.sh - django standard
        monitor.py - restart server when django conf files change
        nailgun/ - django app 
            apps: nailgun.api at api/, nailgun.webui (fully static) at /
            models: recipe, role, release, node, cluster
            tasks.py - django-celery tasks submitted from api/handlers.py: deploy cluster [sub: deploy node]
                MOST IMPORTANT TASK: deploy_cluster
                    Create databags for nodes
                    Provision node with Cobbler
                    ssh node and call /opt/nailgun/bin/deploy
            api/ - nailgun.api django app; JSON API
                main entities in REST API: task, recipe/release/role, node, cluster
                
    scripts/
        agent/ - development scripts to test agent cookbook
        ci/ - scripts for CI, sample-cook - cookbook for testing
    test/ - integration tests [TODO figure out more]
    vagrant/ - cookbooks for use by the vagrant vm
    requirements-deb.txt - debian packages needed for Ubuntu slave node repository
    requirements-rpm.txt - debian packages needed for CentOS slave node repository
    rules.mk - it is just some make macroses
