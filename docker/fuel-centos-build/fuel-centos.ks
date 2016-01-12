install
#url --url=http://127.0.0.1/repo/os/x86_64/
lang en_US.UTF-8
keyboard uk
network --device eth0 --bootproto dhcp
rootpw --iscrypted $1$UKLtvLuY$kka6S665oCFmU7ivSDZzU.
authconfig --enableshadow --passalgo=sha512 --enablefingerprint
selinux --disabled
timezone --utc Etc/UTC
repo --name="Upstream CentOS" --baseurl=http://127.0.0.1/repo/os/x86_64/
repo --name="MOS CentOS" --baseurl=http://127.0.0.1/mos-repo/
%include /root/extra-repos.ks

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
cronie-anacron
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
python-babel
python-ceilometerclient
python-cinderclient
python-crypto
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
mcollective
puppet
rubygem-activesupport
rubygem-amqp
rubygem-mcollective-client
rubygem-symboltable
rubygem-rest-client
rubygem-popen4
rubygem-raemon
rubygem-net-ssh
rubygem-net-ssh-gateway
rubygem-net-ssh-multi
screen
send2syslog
sudo
supervisor
sysstat
tar
tftp-server
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
rpm -e MAKEDEV ethtool upstart iputils policycoreutils iptables \
    iproute

# Remove files that are known to take up lots of space but leave
# directories intact since those may be required by new rpms.

# locales
# nuking the locales breaks things. Lets not do that anymore
# strip most of the languages from the archive.
localedef --delete-from-archive $(localedef --list-archive | \
grep -v -i ^en | xargs )
# prep the archive template
mv /usr/lib/locale/locale-archive  /usr/lib/locale/locale-archive.tmpl
# rebuild archive
/usr/sbin/build-locale-archive
#empty the template
:>/usr/lib/locale/locale-archive.tmpl


#  man pages and documentation
find /usr/share/{man,doc,info,gnome/help} \
        -type f | xargs /bin/rm

#  sln
rm -f /sbin/sln

#  ldconfig
rm -rf /etc/ld.so.cache
rm -rf /var/cache/ldconfig/*
rm -rf /var/cache/yum/* 

# Suppress hiera warnings
mkdir -p /etc/puppet /var/lib/fuel/ibp
touch /etc/puppet/hiera.yaml /var/lib/hiera/common.yaml

# Sudo does not need TTYs
sed -i '/requiretty/s/^/#/g' /etc/sudoers

# Remove all getty services/slices/units (LP#1508364)
find /usr/lib/systemd/system -name "*getty*" -delete

# Mask unecessary services
for service in dev-mqueue.mount dev-hugepages.mount \
    systemd-remount-fs.service sys-kernel-config.mount \
    sys-kernel-debug.mount sys-fs-fuse-connections.mount \
    display-manager.service graphical.target \
    auditd.service firewalld.service \
    network.service network-online.target network.target \
    NetworkManager-wait-online.service NetworkManager.service \
    systemd-logind.service dracut-pre-udev.service \
    systemd-udevd.service swap.target \
    dbus-org.freedesktop.hostname1.service systemd-hostnamed.service \
    proc-sys-fs-binfmt_misc.automount kdump.service \
    cryptsetup.target systemd-modules-load.service \
    tuned.service sysstat.service microcode.service \
    systemd-binfmt.service systemd-reboot.service \
    NetworkManager-dispatcher.service irqbalance.service \
    systemd-initctl.socket systemd-shutdownd.socket \
    system.slice systemd-ask-password-plymouth.path systemd-ask-password-wall.path \
    systemd-journal-flush.service systemd-journald.service systemd-journald.socket; do
  ln -snf /dev/null /etc/systemd/system/${service}
done

# Some services should be disabled instead of masked,
# just because they use in some containers
for service in crond.service rsyslog.service xinetd.service; do
  [ -L /etc/systemd/system/multi-user.target.wants/${service} ] && \
    rm -f /etc/systemd/system/multi-user.target.wants/${service}
done

# Set default target to multi-user.target
ln -snf /usr/lib/systemd/system/multi-user.target /etc/systemd/system/default.target


# Add service that starts start.sh on every container launch
cat << 'EOF' > /etc/systemd/system/start-container.service
[Unit]
Description=Container Startup Script
Requires=dbus.socket
ConditionFileExecutable=/usr/local/bin/start.sh
After=dbus.service

[Service]
Type=oneshot
ExecStart=/bin/bash -c "/usr/local/bin/start.sh > /var/tmp/setup.log 2>&1"
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

%end
