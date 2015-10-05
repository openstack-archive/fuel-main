install
url --url=http://127.0.0.1/os/x86_64/
lang en_US.UTF-8
keyboard uk
network --device eth0 --bootproto dhcp
rootpw --iscrypted $1$UKLtvLuY$kka6S665oCFmU7ivSDZzU.
authconfig --enableshadow --passalgo=sha512 --enablefingerprint
selinux --disabled
timezone --utc Etc/UTC
#repo --name="CentOS" --baseurl=http://mirror.centos.org/centos/6/os/x86_64/ --cost=100
repo --name="Fuel CentOS" --baseurl=http://127.0.0.1/os/x86_64/ --cost 100
#repo --name="Updates" --baseurl=http://mirror.centos.org/centos-6/6/updates/x86_64/ --cost=100
# CentOSPlus is here ONLY for a libselinux patch.
# Once 6.6 is released, this should be removed
# http://lists.centos.org/pipermail/centos-devel/2014-May/010345.html
#repo --name="CentOSPlus" --baseurl=http://mirror.centos.org/centos-6/6/centosplus/x86_64/ --cost=1000

clearpart --all --initlabel
part / --fstype ext4 --size=2048 --grow
reboot
%packages  --excludedocs --nobase
@Core
-MAKEDEV
-aic94xx-firmware
-atmel-firmware
-b43-openfwwf
-bfa-firmware
-dhclient
-efibootmgr
-ethtool
-initscripts
-iproute
-iptables
-iptables-ipv6
-iputils
-ipw2100-firmware
-ipw2200-firmware
-ivtv-firmware
-iwl100-firmware
-iwl1000-firmware
-iwl3945-firmware
-iwl4965-firmware
-iwl5000-firmware
-iwl5150-firmware
-iwl6000-firmware
-iwl6000g2a-firmware
-iwl6050-firmware
-kbd
-kernel-firmware
-libertas-usb8388-firmware
-openssh-server
-postfix
-policycoreutils
-ql2100-firmware
-ql2200-firmware
-ql23xx-firmware
-ql2400-firmware
-ql2500-firmware
-redhat-logos
-rt61pci-firmware
-rt73usb-firmware
-selinux-policy
-selinux-policy-targeted
-upstart
-xorg-x11-drv-ati-firmware
-zd1211-firmware
anacron
bzip2
cobbler
cobbler-web
cronie
crontabs
dnsmasq
fence-agents
fuel-library
httpd
logrotate
nginx
openstack-keystone
openssh-clients
postgresql-server
postgresql-libs
postgresql
python-alembic
python-amqplib
python-anyjson
python-argparse
python-babel
python-ceilometerclient
python-cinderclient
python-crypto
python-daemonize
python-decorator
python-django
python-fabric
python-fysom
python-heatclient
python-iso8601
python-jinja2
python-jsonschema
python-keystoneclient
python-keystonemiddleware
python-kombu
python-mako
python-markupsafe
python-muranoclient
python-netaddr
python-neutronclient
python-netifaces
python-novaclient
python-oslo-config
python-paste
python-ply
python-psycopg2
python-requests
python-saharaclient
python-simplejson
python-six
python-sqlalchemy
python-stevedore
python-urllib3
python-webpy
python-wsgilog
python-wsgiref
PyYAML
python-novaclient
python-networkx-core
pytz
rabbitmq-server
rsync
ruby21-mcollective
ruby21-rubygem-mcollective-client
ruby21-puppet
ruby21-rubygem-activesupport
ruby21-rubygem-amqp
ruby21-rubygem-mcollective-client
ruby21-rubygem-symboltable
ruby21-rubygem-rest-client
ruby21-rubygem-popen4
ruby21-rubygem-raemon
ruby21-rubygem-net-ssh
ruby21-rubygem-net-ssh-gateway
ruby21-rubygem-net-ssh-multi
screen
send2syslog
sudo
supervisor
sysstat
tar
tftp-server
uwsgi-plugin-python
vim-minimal
vim
xinetd
yum-plugin-priorities
%end

%post
# randomize root password and lock root account
dd if=/dev/urandom count=50 | md5sum | passwd --stdin root
passwd -l root

# create necessary devices
/sbin/MAKEDEV /dev/console

# cleanup unwanted stuff

# ami-creator requires grub during the install, so we remove it (and
# its dependencies) in %post
rpm -e grub redhat-logos
rm -rf /boot

# some packages get installed even though we ask for them not to be,
# and they don't have any external dependencies that should make
# anaconda install them
rpm -e MAKEDEV ethtool upstart initscripts iputils policycoreutils iptables \
    iproute

# Remove files that are known to take up lots of space but leave
# directories intact since those may be required by new rpms.

# locales
find
/usr/{{lib,share}/{i18n,locale},{lib,lib64}/gconv,bin/localedef,sbin/build-locale-archive} \
        -type f | xargs /bin/rm

#  man pages and documentation
find /usr/share/{man,doc,info,gnome/help} \
        -type f | xargs /bin/rm

#  cracklib
find /usr/share/cracklib \
        -type f | xargs /bin/rm

#  sln
rm -f /sbin/sln

#  ldconfig
/sbin/ldconfig

%end


