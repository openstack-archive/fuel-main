==========================  For Ubuntu 12.10 server  =============================
-------------------------------  For tests   -------------------------------------
sudo apt-get install python-pip postgresql postgresql-server-dev-all python-dev
sudo apt-get install python-libvirt libvirt-bin virt-manager
sudo apt-get install qemu-utils qemu-kvm pm-utils
virt-manager # for creating pool 'default'
sudo pip install virtualenv
sudo usermod $USER -G libvirtd,sudo
reboot
#check output
kvm-ok
#should be 'KVM acceleration can be used'
cat /sys/module/kvm_intel/parameters/nested
#should be 'Y'
virtualenv venv/fuelweb_test --system-site-packages
. venv/fuelweb_test/bin/activate
pip install -r fuelweb_test/requirements.txt
sudo sed -ir 's/peer/trust/' /etc/postgresql/9.1/main/pg_hba.conf
sudo service postgresql restart
django-admin.py syncdb --settings devops.settings

sh "utils/jenkins/system_tests.sh" -t test -w $(pwd) -j "fuelweb_test" -i "$(pwd)/build/iso/fuelweb-centos-6.4-x86_64.iso" -V $(pwd)/venv/fuelweb_test

# For more information about test run you could use
sh "utils/jenkins/system_tests.sh" -h

------------------------------- For 'make iso' -----------------------------------
http://docs.mirantis.com/fuel-dev/develop/env.html#building-the-fuel-iso

=============== Important notes for Savanna and Murano tests ===============
1. Don't recommend to start tests without kvm
2. Put Savanna image savanna-0.3-vanilla-1.2.1-ubuntu-13.04.qcow2 (md5 9ab37ec9a13bb005639331c4275a308d)
to /tmp/ before start for best performance. If Internet available the image will download automatically.
3. Put Murano image cloud-fedora.qcow2 (md5 6e5e2f149c54b898b3c272f11ae31125) to /tmp/ before start.
Murano image available only internally.
4. Murano tests  without Internet connection on the instances will be failed
5. For Murano tests execute 'export SLAVE_NODE_MEMORY=5120' before tests run.
6. To get heat autoscale tests passed put image F17-x86_64-cfntools.qcow2 in /tmp before start

================ Run single OSTF tests several times ========================
1. Export environment variable OSTF_TEST_NAME. Example: export OSTF_TEST_NAME='Request list of networks'
2. Export environment variable OSTF_TEST_RETRIES_COUNT. Example: export OSTF_TEST_RETRIES_COUNT=120
3. Execute test_ostf_repetable_tests from tests_strength package

sh "utils/jenkins/system_tests.sh" -t test -w $(pwd) -j "fuelweb_test" -i "$ISO_PATH" -V $(pwd)/venv/fuelweb_test -o --group=create_delete_ip_n_times_nova_flat
