cd /tmp
wget http://mirror-fpt-telecom.fpt.net/fedora/epel/6/i386/epel-release-6-8.noarch.rpm
rpm -ivh epel-release-6-8.noarch.rpm

sudo yum -y install unzip
sudo yum -y install python-devel

wget scapy.net
unzip scapy-latest.zip
cd scapy-2.*
sudo python setup.py install

yum -y install tcpdump
yum -y install python-pip
pip-python install nose
