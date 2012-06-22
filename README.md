NAILGUN
=======

How to run Nailgun app from fixtures
------------------------------------

Remove old DB:

`cd nailgun`
`rm -f nailgun.sqlite`

Sync DB:

`./manage.py syncdb --noinput`

Load data from fixtures:

`./manage.py loaddata sample_environment`

Run application:

`./manage.py runserver`

Access Web UI at http://localhost:8000/


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

Testing script is *nailgun/run_tests.sh*
Test cases:
- nailgun/nailgun/tests/test_handlers.py
- nailgun/nailgun/tests/test_models.py

Layout
------

    Makefile - the global product makefile
    Vagrantfile - for the vagrant dev vm
    bin/
        create_release - upload a release json file to nailgun (see e.g. scripts/ci/sample-release.json)
        deploy - invoked on a node to deploy; downloads and executes recipes
        install_cookbook - uploads cookbooks to nailgun admin API
    bootstrap/ - creating a bootstrap image for nodes (initrd, configuration files, packages etc)
    bootstrap2/ - same, another version?
    ci\_with\_libvirt - libvirt-based CI tests
    cookbooks/ - chef cookbooks to be used by nodes.
        agent/ - node agent. Sends ohai data to admin node.
        nailgun/ - nailgun server (not slave node!)
        others obvious
    devops/ - Mirantis CI framework, used by integration tests (./test/integration/). Installed on the master, not slave.
    gnupg/
    iso2/ - creating a bootstrap ISO for nodes [TODO How does it differ from bootstrap/ and bootstrap2/ ?]
    lib/provision/cobbler - apparently unfinished
    nailgun/ - server
        manage.py, run_tests.sh - django standard
        monitor.py - restart server when django conf files change
        nailgun/ - django app 
            apps: nailgun.api at api/, nailgun.webui (fully static) at /
            models: recipe, role, release, node, cluster
            tasks.py - django-celery tasks submitted from api/handlers.py: deploy cluster [sub: deploy node]
                MOST IMPORTANT TASK: deploy_cluster
                    Create databags for nodes
                    Provision node with Cobbler - currently does nothing (?)
                    ssh node and call /opt/nailgun/bin/deploy
            api/ - nailgun.api django app; JSON API
                main entities in REST API: task, recipe/release/role, node, cluster
                
    scripts/
        agent/ - unfinished?
        ci/ - scripts for CI [run on Jenkins? Unfinished?]; looks like scripts check that we can control which cookbooks are installed on nodes.
    test/ - integration tests [TODO figure out more]
    vagrant/ - cookbooks for use by the vagrant vm
    requirements-deb.txt - debian packages needed on nailgun server
    requirements.txt - ?
    rules.mk - ?

