fuelweb-test
============

# Setting up virtual test machine

Steps to set up a virtual machine for running fuelweb selenium tests:

* Create virtual machine with Ubuntu desktop OS. VM should have internet connection. 
  * install java OpenJDK runtime environment.
  * Turn the VM into jenkins node
* Install “git”
* “git clone https://github.com/openstack/fuel-web.git” repository. It will be required in next step (command “cd nailgun” is about folder in this repository)
* Install “postgresql” and “pip”, setup python virtual environement and install python packages. Follow instructions at https://github.com/openstack/fuel-web/blob/master/docs/develop/env.rst#setup-for-nailgun-unit-tests Steps #2 - #5. 
* Install NodeJS. Follow  instructions in step #1 at https://github.com/openstack/fuel-web/blob/master/docs/develop/env.rst#setup-for-web-ui-tests. 
* Try to run fuel-web in fake-ui mode. Follow steps #1 - #3 at https://github.com/openstack/fuel-web/blob/master/docs/develop/env.rst#running-nailgun-in-fake-mode . Try to navigate to http://localhost:8000
* Install next browsers.
  * Chrome
  * Firefox
  * PhantomJS
* Download latest version of Chrome driver from http://chromedriver.storage.googleapis.com/index.html and extract it to home folder at the VM
* “git clone https://github.com/openstack/fuel-main”
  * activate fuel virtual environment “workon fuel”
  * install pip packages “pip install -r fuelweb-test/requirements.txt“
* Try to run selenium tests (fake-ui should be launched).
  * workon fuel
  * export PYTHONPATH=$PYTHONPATH:[path to /fuel-web/nailgun]
  * nosetests fuelweb-test.tests