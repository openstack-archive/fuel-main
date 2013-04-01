sudo pip install virtualenv
virtualenv ../fuelweb_test --system-site-packages
. ../fuelweb_test/bin/activate
pip install -r fuelweb_test/requirements.txt
sudo sed -ir 's/(local\s+all\s+postgres\s+)peer/\1trust/' /etc/postgresql/9.1/main/pg_hba.conf
sudo service postgresql restart
django-admin.py syncdb --settings devops.settings
export ISO=`pwd`/build/iso/nailgun-centos-6.3-amd64.iso
dos.py erase fuelweb
nosetests -w fuelweb_test fuelweb_test.integration.test_node:TestNode.test_network_config
