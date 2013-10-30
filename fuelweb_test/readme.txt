==========================  For Ubuntu 12.10  ================================================
sudo apt-get install python-pip postgresql postgresql-server-dev-all python-dev
sudo pip install virtualenv
virtualenv ../fuelweb_test --system-site-packages
. ../fuelweb_test/bin/activate
cd ..
sudo sed -ir 's/peer/trust/' /etc/postgresql/9.1/main/pg_hba.conf
sudo service postgresql restart
django-admin.py syncdb --settings devops.settings
export ISO_PATH=`pwd`/build/iso/nailgun-centos-6.4-amd64.iso
export ENV_NAME="fuelweb_test" # Or any other name you need
dos.py erase $ENV_NAME
nosetests -w fuelweb_test

