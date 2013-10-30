==========================  For Ubuntu 12.10 server  =============================
-------------------------------  For tests   -------------------------------------
sudo apt-get install python-pip postgresql postgresql-server-dev-all python-dev python-libvirt libvirt-bin virt-manager qemu-utils qemu-kvm
virt-manager # for creating pool default
sudo pip install virtualenv
sudo usermod $USER -G libvirtd,sudo
relogin
virtualenv ../fuelweb_test --system-site-packages
. ../fuelweb_test/bin/activate
cd ..
pip install -r fuelweb_test/requirements.txt
sudo sed -ir 's/peer/trust/' /etc/postgresql/9.1/main/pg_hba.conf
sudo service postgresql restart
django-admin.py syncdb --settings devops.settings
export ISO_PATH=`pwd`/build/iso/fuelweb-centos-6.4-x86_64.iso
export ENV_NAME="fuelweb_test" # Or any other name you need
dos.py erase $ENV_NAME
nosetests -w fuelweb_test

------------------------------- For 'make iso' -----------------------------------
sudo apt-get install yum yum-utils debootstrap bundler libmysqlclient-dev ruby-builder unzip npm python-yaml python-jinja2 mkisofs isomd5sum
sudo npm -g install requirejs
sudo ln -s /usr/bin/nodejs /usr/local/bin/node