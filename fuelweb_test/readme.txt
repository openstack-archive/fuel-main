sudo pip install virtualenv
virtualenv ../fuelweb_test --system-site-packages
. ../fuelweb_test/bin/activate
pip install -r fuelweb_test/requirements.txt
sudo sed -ir 's/(local\s+all\s+postgres\s+)peer/\1trust/' /etc/postgresql/9.1/main/pg_hba.conf
# make sure /etc/postgresql/9.1/main/pg_hba.conf has following line
# local   all             postgres                                trust

sudo service postgresql restart
django-admin.py syncdb --settings devops.settings
export ISO_PATH=`pwd`/build/iso/nailgun-centos-6.4-amd64.iso
export ENV_NAME="fuelweb_test" # Or any other name you need
dos.py erase $ENV_NAME
nosetests -w fuelweb_test
